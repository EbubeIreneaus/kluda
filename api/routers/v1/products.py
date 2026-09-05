from schemas.business import StoreResponseMini
import re
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from models.config import get_db
from models.stock import Stock, StockHistory
from models.business import Store
from models.subscription import UserSubscription
from models.admin.plan import Plan
from schemas.stock import StockCreate, StockUpdate, StockResponse, StockHistoryCreate, StockHistoryResponse
from schemas.user import StaffPermission
from models.user import User
from libs.deps import require_permission, get_staff_store, get_current_user
from libs.audit import record_store_audit
from libs.security import get_client_ip
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from libs.ws_manager import manager as ws_manager
import uuid

router = APIRouter(prefix="/{store_id}/product", tags=["Product"])


def slugify(text: str, prefix="") -> str:
    text = f"{prefix}-{text}".lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


@router.post("", response_model=StockResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=StockResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def create_stock(
    stock_data: StockCreate,
    store_id: uuid.UUID,
    request: Request,
    store: StoreResponseMini = Depends(get_staff_store),
    db: AsyncSession = Depends(get_db),
    staff_id: str = Query(default="unknown", description="Staff ID for WS broadcast exclusion"),
    actor: User = Depends(require_permission(StaffPermission.CREATE_PRODUCT)),
):
    db_store = await db.scalar(select(Store).where(Store.store_id == store.store_id))
    owner_user_id = db_store.user_id if db_store else None
    owner = await db.scalar(select(User).where(User.user_id == owner_user_id)) if owner_user_id else None
    current_sub = None
    if owner and owner.current_subscription_id:
        current_sub = await db.scalar(
            select(UserSubscription).where(
                UserSubscription.subscription_id == owner.current_subscription_id
            )
        )
    plan = None
    if current_sub and current_sub.plan_id:
        plan = await db.scalar(select(Plan).where(Plan.slug == current_sub.plan_id))
    if not plan:
        plan = await db.scalar(select(Plan).where(Plan.slug == "free"))

    product_limit = plan.product_limit if plan else 100
    if product_limit and product_limit > 0 and owner_user_id:
        total_products = (
            await db.scalar(
                select(func.count(Stock.id))
                .join(Store, Stock.store_id == Store.store_id)
                .where(Store.user_id == owner_user_id, Stock.deleted == False)
            )
        ) or 0
        if total_products >= product_limit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Product catalog limit reached ({product_limit} products). Upgrade your subscription plan to add more items.",
            )
    barcode = stock_data.barcode_id.strip() if stock_data.barcode_id and stock_data.barcode_id.strip() else None
    if barcode:
        existing_barcode = await db.execute(
            select(Stock).where(
                Stock.barcode_id == barcode,
                Stock.deleted == False,
                Stock.store_id == store.store_id
            )
        )
        if existing_barcode.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A product with barcode '{stock_data.barcode_id}' already exists",
            )

    slug = slugify(stock_data.name, prefix=store.name[::4])

    existing = await db.execute(select(Stock).where(Stock.slug == slug, Stock.store_id == store.store_id))
    if existing.scalar_one_or_none():
        slug = f"{slug}-{int(datetime.now(timezone.utc).timestamp())}"

    new_stock = Stock(
        name=stock_data.name,
        **stock_data.model_dump(
            exclude_none=True, exclude_unset=True, exclude={"name", "slug", "barcode_id"}
        ),
        slug=slug,
        store_id = store.store_id,
        barcode_id=barcode
    )

    db.add(new_stock)
    await db.flush()

    await db.refresh(new_stock)

    await record_store_audit(
        db=db,
        store_id=store.store_id,
        action="product.create",
        target_type="product",
        actor=actor,
        target_id=new_stock.slug,
        target_name=new_stock.name,
        details={
            "unit_price": float(new_stock.unit_price) if new_stock.unit_price is not None else None,
            "quantities": float(new_stock.quantities) if new_stock.quantities is not None else None,
            "cost_price": float(new_stock.cost_price) if new_stock.cost_price is not None else None,
            "barcode_id": new_stock.barcode_id,
        },
        ip_address=get_client_ip(request),
    )

    await ws_manager.broadcast(
        store.store_id,
        {"event": "add_product", "data": StockResponse.model_validate(new_stock).model_dump(mode="json")},
    )
    return new_stock


@router.post("/stock-history", response_model=StockHistoryResponse, status_code=status.HTTP_201_CREATED)
async def create_stock_history(
    store_id: uuid.UUID,
    history_data: StockHistoryCreate,
    request: Request,
    store: StoreResponseMini = Depends(get_staff_store),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(StaffPermission.ADJUST_STOCK)),
):
    res = await db.execute(
        select(Stock).where(
            Stock.slug == history_data.stock_slug,
            Stock.store_id == store.store_id,
            Stock.deleted == False
        )
    )
    product = res.scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with slug '{history_data.stock_slug}' not found",
        )

    if history_data.quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity must be greater than zero",
        )

    current_qty = float(product.quantities or 0)
    if history_data.action_type == "addition":
        new_qty = current_qty + float(history_data.quantity)
    else:
        new_qty = current_qty - float(history_data.quantity)

    product.quantities = new_qty

    history_record = StockHistory(
        stock_slug=history_data.stock_slug,
        quantity=history_data.quantity,
        action_type=history_data.action_type,
        reason=history_data.reason,
        note=history_data.note,
        user_id=user.user_id,
        store_id=store.store_id
    )
    db.add(history_record)
    await db.flush()
    await db.refresh(history_record)
    await db.refresh(product)

    await record_store_audit(
        db=db,
        store_id=store.store_id,
        action="stock.adjust",
        target_type="stock",
        actor=user,
        target_id=product.slug,
        target_name=product.name,
        details={
            "action_type": history_data.action_type,
            "quantity": float(history_data.quantity),
            "previous_quantity": current_qty,
            "new_quantity": new_qty,
            "reason": history_data.reason,
            "note": history_data.note,
        },
        ip_address=get_client_ip(request),
    )

    await ws_manager.broadcast(
        store.store_id,
        {
            "event": "update_product",
            "data": StockResponse.model_validate(product).model_dump(mode="json")
        },
    )

    return history_record


@router.get("/stock-history", response_model=list[StockHistoryResponse])
async def get_stock_histories(
    store_id: uuid.UUID,
    slug: str | None = Query(None, description="Filter history by product slug"),
    limit: int = Query(50, ge=1, le=200),
    store: StoreResponseMini = Depends(get_staff_store),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(StaffPermission.VIEW_PRODUCT)),
):
    stmt = select(StockHistory).where(StockHistory.store_id == store.store_id).order_by(StockHistory.created_at.desc()).limit(limit)
    if slug:
        stmt = stmt.where(StockHistory.stock_slug == slug)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("", response_model=list[StockResponse])
@router.get("/", response_model=list[StockResponse], include_in_schema=False)
async def get_stocks(
    store_id: uuid.UUID,
    store: StoreResponseMini = Depends(get_staff_store),
    search: str | None = Query(
        None, description="Search products by name, description, SKU or barcode"
    ),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(StaffPermission.VIEW_PRODUCT)),
):
    stmt = select(Stock).where(Stock.deleted == False, Stock.store_id == store.store_id)

    if search and search.strip():
        terms = [re.sub(r"[^\w]", "", term) for term in search.split() if term.strip()]
        terms = [t for t in terms if t]
        if terms:
            query_str = " | ".join([f"{term}:*" for term in terms])
            text_vector = func.to_tsvector(
                "english",
                func.coalesce(Stock.name, "")
                + " "
                + func.coalesce(Stock.description, "")
                + " "
                + func.coalesce(Stock.sku, "")
                + " "
                + func.coalesce(Stock.barcode_id, ""),
            )
            ts_query = func.to_tsquery("english", query_str)
            rank = func.ts_rank(text_vector, ts_query)

            stmt = stmt.where(text_vector.op("@@")(ts_query)).order_by(
                rank.desc(), Stock.created_at.desc()
            )
        else:
            stmt = stmt.order_by(Stock.created_at.desc())
    else:
        stmt = stmt.order_by(Stock.created_at.desc())

    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("/{slug}", response_model=StockResponse)
async def get_stock(
    slug: str,
    store_id: uuid.UUID,
    store: StoreResponseMini = Depends(get_staff_store),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(StaffPermission.VIEW_PRODUCT)),
):
    res = await db.execute(
        select(Stock).where(Stock.slug == slug, Stock.deleted == False, Stock.store_id == store.store_id)
    )
    stock = res.scalar_one_or_none()

    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with slug '{slug}' not found",
        )

    return stock


@router.put("/{slug}")
async def update_stock(
    store_id: uuid.UUID,
    slug: str,
    update_data: StockUpdate,
    request: Request,
    store: StoreResponseMini = Depends(get_staff_store),
    db: AsyncSession = Depends(get_db),
    staff_id: str = Query(default="unknown", description="Staff ID for WS broadcast exclusion"),
    actor: User = Depends(require_permission(StaffPermission.EDIT_PRODUCT)),
):
    res = await db.execute(select(Stock).where(Stock.slug == slug, Stock.store_id == store.store_id))
    stock = res.scalar_one_or_none()
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with slug '{slug}' not found",
        )

    values = update_data.model_dump(exclude_unset=True, exclude={"quantities"})
    if "barcode_id" in update_data.model_fields_set:
        clean_barcode = update_data.barcode_id.strip() if update_data.barcode_id and update_data.barcode_id.strip() else None
        if clean_barcode:
            existing_barcode = await db.execute(
                select(Stock).where(
                    Stock.barcode_id == clean_barcode,
                    Stock.slug != slug,
                    Stock.deleted == False,
                    Stock.store_id == store.store_id
                )
            )
            if existing_barcode.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"A product with barcode '{clean_barcode}' already exists",
                )
        values["barcode_id"] = clean_barcode

    clean_values = {k: v for k, v in values.items() if v is not None or k == "barcode_id"}
    if clean_values:
        old_values = {}
        for k in clean_values.keys():
            old_val = getattr(stock, k, None)
            if isinstance(old_val, (int, float)) or hasattr(old_val, "as_tuple"):
                old_values[k] = float(old_val)
            else:
                old_values[k] = str(old_val) if old_val is not None else None

        changes = {}
        for k, v in clean_values.items():
            new_val = float(v) if isinstance(v, (int, float)) or hasattr(v, "as_tuple") else str(v) if v is not None else None
            changes[k] = {"old": old_values.get(k), "new": new_val}

        await db.execute(update(Stock).values(**clean_values).where(Stock.slug == slug))

        await record_store_audit(
            db=db,
            store_id=store.store_id,
            action="product.update",
            target_type="product",
            actor=actor,
            target_id=stock.slug,
            target_name=stock.name,
            details={"changes": changes},
            ip_address=get_client_ip(request),
        )

    await db.flush()
    await db.refresh(stock)
    await ws_manager.broadcast(
        store.store_id,
        {"event": "update_product", "data": StockResponse.model_validate(stock).model_dump(mode="json")},
    )
    return {"success": True}


@router.delete("/{slug}")
async def delete_stock(
    slug: str,
    store_id: uuid.UUID,
    request: Request,
    store: StoreResponseMini = Depends(get_staff_store),
    db: AsyncSession = Depends(get_db),
    staff_id: str = Query(default="unknown", description="Staff ID for WS broadcast exclusion"),
    actor: User = Depends(require_permission(StaffPermission.DELETE_PRODUCT)),
):
    res = await db.execute(select(Stock).where(Stock.slug == slug, Stock.store_id==store.store_id))
    stock = res.scalar_one_or_none()

    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with slug '{slug}' not found",
        )

    stock.deleted = True
    stock.deleted_at = datetime.now(timezone.utc)
    await db.flush()

    await record_store_audit(
        db=db,
        store_id=store.store_id,
        action="product.delete",
        target_type="product",
        actor=actor,
        target_id=stock.slug,
        target_name=stock.name,
        details={
            "price": float(stock.price) if stock.price is not None else None,
            "quantities": float(stock.quantities) if stock.quantities is not None else None,
            "barcode_id": stock.barcode_id,
        },
        ip_address=get_client_ip(request),
    )

    await ws_manager.broadcast(
        store.store_id,
        {"event": "delete_product", "data": {"slug": slug}},
    )
    return {"message": f"Product '{slug}' deleted successfully"}
