import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from models.config import get_db
from models.business import Store
from models.user import User, Staff
from models.stock import Stock, Sale
from models.admin.user import Admin
from schemas.admin.store import AdminStoreListItem, AdminStoreDetailResponse, AdminStoreStatusUpdateRequest
from schemas.admin.user import AdminPermission
from schemas.business import StoreStatus
from libs.deps import require_admin_permission
from libs.audit import record_audit_log


router = APIRouter(prefix="/stores", tags=["Admin Store Moderation"])


@router.get("", response_model=list[AdminStoreListItem])
async def list_stores(
    search: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    category_filter: str | None = Query(None, alias="category"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_admin_permission(AdminPermission.MANAGE_STORES)),
):
    stmt = select(Store)
    if search:
        stmt = stmt.where(Store.name.ilike(f"%{search}%"))
    if status_filter:
        stmt = stmt.where(Store.status == status_filter)
    if category_filter:
        stmt = stmt.where(Store.category == category_filter)

    stmt = stmt.order_by(Store.created_at.desc()).limit(limit).offset(offset)
    stores = (await db.scalars(stmt)).all()

    items = []
    for s in stores:
        staff_count = await db.scalar(select(func.count(Staff.id)).where(Staff.store_id == s.store_id)) or 0
        product_count = await db.scalar(select(func.count(Stock.id)).where(Stock.store_id == s.store_id)) or 0
        sales_stats = await db.execute(
            select(
                func.count(Sale.id).label("total_sales"),
                func.coalesce(func.sum(Sale.amount_recived), 0).label("total_rev")
            ).where(Sale.store_id == s.store_id)
        )
        stats_row = sales_stats.first()
        total_sales_count = stats_row.total_sales if stats_row else 0
        total_revenue = int(stats_row.total_rev) if stats_row else 0

        items.append(
            AdminStoreListItem(
                id=s.id,
                store_id=s.store_id,
                owner_id=s.user_id,
                name=s.name,
                category=s.category,
                status=s.status.value if hasattr(s.status, 'value') else str(s.status),
                staff_count=staff_count,
                product_count=product_count,
                total_sales_count=total_sales_count,
                total_revenue=total_revenue,
                created_at=s.created_at,
            )
        )
    return items


@router.get("/{store_id}", response_model=AdminStoreDetailResponse)
async def get_store_detail(
    store_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_admin_permission(AdminPermission.MANAGE_STORES)),
):
    store = await db.scalar(select(Store).where(Store.store_id == store_id))
    if not store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")

    owner = await db.scalar(select(User).where(User.user_id == store.user_id))
    staff_count = await db.scalar(select(func.count(Staff.id)).where(Staff.store_id == store.store_id)) or 0
    product_count = await db.scalar(select(func.count(Stock.id)).where(Stock.store_id == store.store_id)) or 0
    sales_stats = await db.execute(
        select(
            func.count(Sale.id).label("total_sales"),
            func.coalesce(func.sum(Sale.amount_recived), 0).label("total_rev")
        ).where(Sale.store_id == store.store_id)
    )
    stats_row = sales_stats.first()

    return AdminStoreDetailResponse(
        id=store.id,
        store_id=store.store_id,
        owner_id=store.user_id,
        owner_name=owner.fullname if owner else None,
        owner_email=owner.email if owner else None,
        name=store.name,
        address=store.address,
        category=store.category,
        currency=store.currency or "NGN",
        status=store.status.value if hasattr(store.status, 'value') else str(store.status),
        staff_count=staff_count,
        product_count=product_count,
        total_sales_count=stats_row.total_sales if stats_row else 0,
        total_revenue=int(stats_row.total_rev) if stats_row else 0,
        created_at=store.created_at,
        updated_at=store.updated_at,
    )


@router.put("/{store_id}/status", response_model=AdminStoreDetailResponse)
async def update_store_status(
    store_id: uuid.UUID,
    payload: AdminStoreStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_admin_permission(AdminPermission.MANAGE_STORES)),
):
    store = await db.scalar(select(Store).where(Store.store_id == store_id))
    if not store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")

    old_status = store.status.value if hasattr(store.status, 'value') else str(store.status)
    store.status = StoreStatus(payload.status) if payload.status in [s.value for s in StoreStatus] else payload.status
    await db.flush()
    await db.refresh(store)

    await record_audit_log(
        db=db,
        admin_id=admin.admin_id,
        action="STORE_STATUS_UPDATED",
        target_type="store",
        target_id=store.store_id,
        details={"old_status": old_status, "new_status": payload.status, "reason": payload.reason},
    )

    owner = await db.scalar(select(User).where(User.user_id == store.user_id))
    staff_count = await db.scalar(select(func.count(Staff.id)).where(Staff.store_id == store.store_id)) or 0
    product_count = await db.scalar(select(func.count(Stock.id)).where(Stock.store_id == store.store_id)) or 0
    sales_stats = await db.execute(
        select(
            func.count(Sale.id).label("total_sales"),
            func.coalesce(func.sum(Sale.amount_recived), 0).label("total_rev")
        ).where(Sale.store_id == store.store_id)
    )
    stats_row = sales_stats.first()

    return AdminStoreDetailResponse(
        id=store.id,
        store_id=store.store_id,
        owner_id=store.user_id,
        owner_name=owner.fullname if owner else None,
        owner_email=owner.email if owner else None,
        name=store.name,
        address=store.address,
        category=store.category,
        currency=store.currency or "NGN",
        status=store.status.value if hasattr(store.status, 'value') else str(store.status),
        staff_count=staff_count,
        product_count=product_count,
        total_sales_count=stats_row.total_sales if stats_row else 0,
        total_revenue=int(stats_row.total_rev) if stats_row else 0,
        created_at=store.created_at,
        updated_at=store.updated_at,
    )
