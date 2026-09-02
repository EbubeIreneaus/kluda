from models.stock import Stock, Sale
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
from schemas.business import StoreStatus
from schemas.user import UserResponseMini, StaffStatus
from sqlalchemy import update, select, func
from schemas.business import StoreUpdate, StoreCreate, StoreResponseMini
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, status, HTTPException, Depends, Request
from libs.deps import get_current_user, get_staff_store
from models.config import get_db
from models.business import Store
from models.user import User, StoreMember
from models.subscription import UserSubscription
from models.admin.plan import Plan
from routers.v1.auth import get_user_stores
import uuid

router = APIRouter(prefix="/store", tags=["Store Management"])


@router.post("")
@router.post("/", include_in_schema=False)
async def create_store(
    body: StoreCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StoreResponseMini:
    current_sub = None
    if user.current_subscription_id:
        current_sub = await db.scalar(
            select(UserSubscription).where(
                UserSubscription.subscription_id == user.current_subscription_id
            )
        )
    plan = None
    if current_sub and current_sub.plan_id:
        plan = await db.scalar(select(Plan).where(Plan.slug == current_sub.plan_id))
    if not plan:
        plan = await db.scalar(select(Plan).where(Plan.slug == "free"))

    store_limit = plan.store_limit if plan else 1
    if store_limit and store_limit > 0:
        existing_count = (
            await db.scalar(
                select(func.count(Store.id)).where(
                    Store.user_id == user.user_id, Store.status == StoreStatus.ACTIVE
                )
            )
        ) or 0
        if existing_count >= store_limit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Store branch limit reached ({store_limit} store branches). Upgrade your subscription plan to create more branches.",
            )

    store = Store(
        **body.model_dump(),
        user_id=user.user_id,
        status=StoreStatus.ACTIVE,
    )
    db.add(store)
    await db.flush()

    member_entry = StoreMember(
        store_id=store.store_id,
        user_id=user.user_id,
        role="owner",
        permission=["manage:all"],
        status=StaffStatus.ACTIVE,
    )
    db.add(member_entry)
    await db.commit()
    await db.refresh(store)

    return store


@router.get("")
@router.get("/", include_in_schema=False)
async def get_stores(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stores = await get_user_stores(user.user_id, db)
    return stores


@router.patch("/{store_id}")
@router.put("/{store_id}")
async def update_store(
    store_id: uuid.UUID,
    body: StoreUpdate,
    store: StoreResponseMini = Depends(get_staff_store),
    db: AsyncSession = Depends(get_db),
):
    stmt = update(Store).where(Store.store_id == store.store_id).values(
        **body.model_dump(exclude_unset=True, exclude_none=True)
    )
    await db.execute(stmt)
    await db.commit()
    return {"success": True}


@router.get("/{store_id}")
async def get_store_details(
    store_id: uuid.UUID,
    store: StoreResponseMini = Depends(get_staff_store),
    db: AsyncSession = Depends(get_db),
):
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    sales = (
        await db.scalars(
            select(Sale)
            .options(selectinload(Sale.items))
            .where(Sale.store_id == store.store_id, Sale.created_at >= today)
        )
    ).all()

    stocks = (
        await db.scalars(
            select(Stock).where(
                Stock.store_id == store.store_id, Stock.deleted == False
            )
        )
    ).all()

    return {
        **store.model_dump(),
        "stocks": stocks,
        "sales": sales,
    }


@router.delete("/{store_id}")
async def delete_store(
    request: Request,
    store_id: uuid.UUID,
    store: StoreResponseMini = Depends(get_staff_store),
    db: AsyncSession = Depends(get_db),
):
    reason = None
    try:
        req_json = await request.json()
        reason = req_json.get("reason", None)
    except Exception:
        pass

    await db.execute(
        update(Store).where(Store.store_id == store.store_id).values(
            status=StoreStatus.DELETED, delete_reason=reason
        )
    )
    await db.commit()
    return {"success": True}
