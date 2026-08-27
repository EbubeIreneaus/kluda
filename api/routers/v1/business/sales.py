from schemas.business import StoreResponseMini
import uuid
import logging
from datetime import date, datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, and_
from sqlalchemy.orm import joinedload
from models.config import get_db
from models.stock import Sale, SaleItem, Stock
from models.user import Customer, Debt, Staff
from schemas.stock import SaleCreate, SaleUpdate, SaleResponse
from schemas.user import StaffPermission
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from libs.ws_manager import manager as ws_manager
from libs.deps import require_permission, get_staff, get_staff_store
from libs.notification_manager import notification_manager
import uuid

router = APIRouter(prefix="/{store_id}/sales", tags=["Sales"])


@router.get("/ping")
async def ping(
    store_id: uuid.UUID,
    store: StoreResponseMini = Depends(get_staff_store),
    db: AsyncSession = Depends(get_db),
):
    try:
        res = await db.execute(
            select(func.count())
            .select_from(Stock)
            .where(Stock.store_id == store.store_id)
        )
        count = res.scalar()
        return {"status": "ok", "db_connected": True, "product_count": count}
    except Exception as e:
        logging.error(f"Database ping failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database connection error: {str(e)}",
        )


@router.post("", status_code=status.HTTP_201_CREATED)
@router.post("/", status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def create_sales_batch(
    sales_data: list[SaleCreate],
    store_id: uuid.UUID,
    store: StoreResponseMini = Depends(get_staff_store),
    db: AsyncSession = Depends(get_db),
    staff_id: str = Query(
        default="unknown", description="Staff ID for WS broadcast exclusion"
    ),
    _: Staff = Depends(require_permission(StaffPermission.RECORD_SALES)),
):
    created_ids = []
    synced_keys = []
    failed = []
    low_stock_alerts = []
    debt_alerts = []

    for sale_data in sales_data:
        try:
            async with db.begin_nested():
                # 1. Check idempotency
                stmt = select(Sale).where(
                    Sale.idempotency_key == sale_data.idempotency_key,
                    Sale.store_id == store.store_id
                )
                existing_sale = (await db.execute(stmt)).scalar_one_or_none()
                if existing_sale:
                    synced_keys.append(str(sale_data.idempotency_key))
                    continue 

                customer = None
                if sale_data.customer_id:
                    c_res = await db.execute(
                        select(Customer).where(
                            Customer.customer_id == sale_data.customer_id,
                            Customer.store_id == store.store_id
                        )
                    )
                    customer = c_res.scalar_one_or_none()
                    if not customer:
                        if sale_data.payment_method == "debt":
                            raise HTTPException(
                                status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Customer with ID '{sale_data.customer_id}' not found for debt payment",
                            )
                        else:
                            sale_data.customer_id = None

   
                new_sale = Sale(
                    discount=sale_data.discount,
                    customer_id=sale_data.customer_id,
                    store_id=store.store_id,
                    payment_method=sale_data.payment_method,
                    amount_recived=sale_data.amount_recived,
                    idempotency_key=sale_data.idempotency_key,
                    staff_note=sale_data.staff_note,
                    status=sale_data.status,
                )
                db.add(new_sale)
                await db.flush()

                sale_id = new_sale.sale_id

                items_to_add = []
                note_parts = []
                grand_total = 0

                for item_in in sale_data.items:
                    stk_res = await db.execute(
                        select(Stock).where(Stock.slug == item_in.stock_slug)
                    )
                    stock_item = stk_res.scalar_one_or_none()
                    if not stock_item:
                        clean_name = item_in.stock_slug.replace("-", " ").title()
                        stock_item = Stock(
                            name=f"[Archived] {clean_name}",
                            slug=item_in.stock_slug,
                            unit_price=item_in.amount,
                            quantities=0,
                            unit_in="piece",
                            deleted=True,
                        )
                        db.add(stock_item)
                        await db.flush()

                    # Format for debt note: e.g. "3 piece of Peak Milk Powder 400g"
                    qty_str = (
                        str(int(item_in.quantities))
                        if item_in.quantities.is_integer()
                        else str(item_in.quantities)
                    )
                    unit_in = stock_item.unit_in or "pcs"
                    note_parts.append(f"{qty_str} {unit_in} of {stock_item.name}")

                    grand_total += int(item_in.amount * item_in.quantities)

                    if sale_data.status == "completed" and not stock_item.deleted:
                        stock_item.quantities = max(
                            0.0,
                            float(stock_item.quantities) - float(item_in.quantities),
                        )
                        min_alert = float(stock_item.min_stock_alert if hasattr(stock_item, "min_stock_alert") and stock_item.min_stock_alert is not None else 5)
                        if float(stock_item.quantities) <= min_alert:
                            low_stock_alerts.append((stock_item.name, int(stock_item.quantities), int(min_alert)))

                    sale_item = SaleItem(
                        sale_id=sale_id,
                        stock_slug=stock_item.slug,
                        amount=item_in.amount,
                        quantities=item_in.quantities,
                    )
                    items_to_add.append(sale_item)

                db.add_all(items_to_add)
                await db.flush()

                grand_total = max(0, grand_total - sale_data.discount)

                if sale_data.payment_method == "debt":
                    if not customer:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Customer is required for debt payments",
                        )
                    debt_amount = max(0, grand_total - sale_data.amount_recived)
                    debt_note = ", ".join(note_parts)
                    new_debt = Debt(
                        customer_id=sale_data.customer_id,
                        amount=debt_amount,
                        note=debt_note,
                        status="unpaid",
                        staff_note=sale_data.staff_note,
                    )
                    db.add(new_debt)
                    await db.flush()

                    debt_alerts.append((customer.name or "Customer", float(debt_amount), float((customer.total_debt or 0) + debt_amount)))

                created_ids.append(sale_id)
                synced_keys.append(str(sale_data.idempotency_key))

        except Exception as e:
            logging.error(
                f"Error processing sale {sale_data.idempotency_key}: {str(e)}"
            )
            failed.append(
                {
                    "idempotency_key": str(sale_data.idempotency_key),
                    "reason": str(e),
                }
            )

    await db.commit()

    for sid in created_ids:
        await ws_manager.broadcast(
            store.store_id,
            {"event": "add_sale", "data": {"sale_id": str(sid)}},
        )

    for item_name, current_qty, min_qty in low_stock_alerts:
        await notification_manager.enqueue_low_stock(store.store_id, item_name, current_qty, min_qty)

    for cust_name, d_amt, tot_d in debt_alerts:
        await notification_manager.enqueue_credit_sale(store.store_id, cust_name, d_amt, tot_d)

    return {
        "success": True,
        "created_count": len(created_ids),
        "created_ids": [str(x) for x in created_ids],
        "synced_keys": synced_keys,
        "failed": failed,
    }


@router.get("/analytics")
async def get_analytics(
    store_id: uuid.UUID,
    store: StoreResponseMini = Depends(get_staff_store),
    period: str = Query(
        default="today",
        description="One of: today, week, month, 3month, 6month, 12month, or 'custom'",
    ),
    date_from: date | None = Query(
        default=None, description="Start date (YYYY-MM-DD) when period=custom"
    ),
    date_to: date | None = Query(
        default=None, description="End date (YYYY-MM-DD) when period=custom"
    ),
    db: AsyncSession = Depends(get_db),
    _: Staff = Depends(require_permission(StaffPermission.VIEW_ANALYTICS)),
):
    """Aggregate analytics for the given period."""
    today = datetime.now(timezone.utc).date()

    if period == "custom":
        if not date_from or not date_to:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="date_from and date_to are required when period=custom",
            )
        start = datetime(
            date_from.year, date_from.month, date_from.day, tzinfo=timezone.utc
        )
        end = datetime(
            date_to.year, date_to.month, date_to.day, 23, 59, 59, tzinfo=timezone.utc
        )
    else:
        offsets = {
            "today": 0,
            "week": 6,
            "month": 29,
            "3month": 89,
            "6month": 179,
            "12month": 364,
        }
        days_back = offsets.get(period, 0)
        from_date = today - timedelta(days=days_back)
        start = datetime(
            from_date.year, from_date.month, from_date.day, tzinfo=timezone.utc
        )
        end = datetime(
            today.year, today.month, today.day, 23, 59, 59, tzinfo=timezone.utc
        )

    base_cond = and_(
        Sale.created_at >= start, Sale.created_at <= end, Sale.status != "cancelled", Sale.store_id==store.store_id
    )

    rev_res = await db.execute(
        select(
            func.count(Sale.sale_id).label("count"),
            func.coalesce(func.sum(Sale.amount_recived), 0).label("received"),
        ).where(base_cond)
    )
    rev_row = rev_res.one()
    total_transactions = int(rev_row.count)

    items_res = await db.execute(
        select(
            Sale.sale_id,
            Sale.discount,
            func.sum(SaleItem.amount * SaleItem.quantities).label("subtotal"),
        )
        .join(SaleItem, SaleItem.sale_id == Sale.sale_id)
        .where(base_cond)
        .group_by(Sale.sale_id, Sale.discount)
    )
    total_revenue = 0
    for row in items_res:
        total_revenue += max(0, int(row.subtotal) - int(row.discount))

    method_res = await db.execute(
        select(Sale.payment_method, func.count(Sale.sale_id).label("cnt"))
        .where(base_cond)
        .group_by(Sale.payment_method)
    )
    payment_breakdown = {row.payment_method: int(row.cnt) for row in method_res}

    top_res = await db.execute(
        select(
            Stock.name,
            func.sum(SaleItem.quantities).label("total_qty"),
            func.sum(SaleItem.amount * SaleItem.quantities).label("total_revenue"),
        )
        .join(SaleItem, SaleItem.stock_slug == Stock.slug)
        .join(Sale, Sale.sale_id == SaleItem.sale_id)
        .where(base_cond)
        .group_by(Stock.name)
        .order_by(func.sum(SaleItem.quantities).desc())
        .limit(10)
    )
    top_products = [
        {
            "name": row.name,
            "qty": float(row.total_qty),
            "revenue": int(row.total_revenue),
        }
        for row in top_res
    ]

    series_res = await db.execute(
        select(
            func.date(Sale.created_at).label("day"),
            func.count(Sale.sale_id).label("cnt"),
        )
        .where(base_cond)
        .group_by(func.date(Sale.created_at))
        .order_by(func.date(Sale.created_at))
    )
    daily_series = [{"date": str(row.day), "count": int(row.cnt)} for row in series_res]

    rev_series_res = await db.execute(
        select(
            func.date(Sale.created_at).label("day"),
            Sale.sale_id,
            Sale.discount,
            func.sum(SaleItem.amount * SaleItem.quantities).label("subtotal"),
        )
        .join(SaleItem, SaleItem.sale_id == Sale.sale_id)
        .where(base_cond)
        .group_by(func.date(Sale.created_at), Sale.sale_id, Sale.discount)
        .order_by(func.date(Sale.created_at))
    )
    daily_revenue: dict[str, int] = {}
    for row in rev_series_res:
        day = str(row.day)
        daily_revenue[day] = daily_revenue.get(day, 0) + max(
            0, int(row.subtotal) - int(row.discount)
        )
    revenue_series = [
        {"date": d, "revenue": v} for d, v in sorted(daily_revenue.items())
    ]

    return {
        "period": period,
        "date_from": str(start.date()),
        "date_to": str(end.date()),
        "total_revenue": total_revenue,
        "total_transactions": total_transactions,
        "payment_breakdown": payment_breakdown,
        "top_products": top_products,
        "daily_series": daily_series,
        "revenue_series": revenue_series,
    }


@router.get("", response_model=Page[SaleResponse])
@router.get("/", response_model=Page[SaleResponse], include_in_schema=False)
async def get_sales(
    store_id: uuid.UUID,
    store: StoreResponseMini = Depends(get_staff_store),
    sale_date: date | None = Query(
        default=None,
        description="Filter sales by date (YYYY-MM-DD). Defaults to today.",
    ),
    db: AsyncSession = Depends(get_db),
    _: Staff = Depends(get_staff),
):
    """Return paginated sales filtered to a single calendar day (default = today)."""
    target = sale_date or datetime.now(timezone.utc).date()
    day_start = datetime(target.year, target.month, target.day, tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)

    stmt = (
        select(Sale)
        .options(
            joinedload(Sale.items).joinedload(SaleItem.stock),
            joinedload(Sale.customer),
        )
        .where(and_(Sale.created_at >= day_start, Sale.created_at < day_end), Sale.store_id == store.store_id)
        .order_by(Sale.created_at.desc())
    )
    return await paginate(db, stmt)


@router.get("/{sale_id}", response_model=SaleResponse)
async def get_sale(
    sale_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: Staff = Depends(get_staff),
):
    res = await db.execute(
        select(Sale)
        .options(
            joinedload(Sale.items).joinedload(SaleItem.stock), joinedload(Sale.customer)
        )
        .where(Sale.sale_id == sale_id)
    )
    sale = res.scalar_one_or_none()

    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sale transaction '{sale_id}' not found",
        )

    return sale


@router.put("/{sale_id}")
async def update_sale(
    sale_id: uuid.UUID,
    update_data: SaleUpdate,
    db: AsyncSession = Depends(get_db),
    _: Staff = Depends(require_permission(StaffPermission.RECORD_SALES)),
):
    res = await db.execute(select(Sale).where(Sale.sale_id == sale_id))
    if not res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sale transaction '{sale_id}' not found",
        )

    values = update_data.model_dump(exclude_unset=True, exclude_none=True)
    if values:
        await db.execute(update(Sale).values(**values).where(Sale.sale_id == sale_id))

    return {"success": True}


@router.delete("/{sale_id}")
async def delete_sale(
    sale_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: Staff = Depends(require_permission(StaffPermission.RECORD_SALES)),
):
    res = await db.execute(select(Sale).where(Sale.sale_id == sale_id))
    sale = res.scalar_one_or_none()

    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sale transaction '{sale_id}' not found",
        )

    sale.status = "cancelled"
    return {"message": f"Sale '{sale_id}' marked as cancelled"}
