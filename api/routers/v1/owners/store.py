from models.stock import Stock, Sale
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
from schemas.business import StoreStatus
from schemas.user import UserResponseMini
from sqlalchemy import update, select
from schemas.business import StoreUpdate
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, status, HTTPException, Depends, Request, Query
from libs.deps import get_user, get_store
from models.config import get_db
from models.business import Store
from schemas.business import StoreCreate, StoreResponseMini
import uuid

router = APIRouter(prefix="/store")

@router.post("")
async def create_store(
    body: StoreCreate,
    user = Depends(get_user),
    db: AsyncSession = Depends(get_db)
) -> StoreResponseMini:

    store = Store(
        **body.model_dump(),
        user_id = user.user_id
    )

    db.add(store)
    await db.flush()

    return store

@router.get("")
async def get_stores(
    user: UserResponseMini = Depends(get_user),
    db: AsyncSession = Depends(get_db)
) -> list[StoreResponseMini]:
    # might want to implement redis in the future

    stores = await db.scalars(
        select(Store).where(Store.user_id ==user.user_id, Store.status != StoreStatus.DELETED)
    )

    return stores

@router.patch("/{store_id}")
@router.put("/{store_id}")
async def update_store(
    store_id: uuid.UUID,
    body: StoreUpdate,
    store: StoreResponseMini = Depends(get_store),
    db: AsyncSession = Depends(get_db)
):
    stmt = update(Store).where(Store.store_id == store.store_id).values(
        **body.model_dump(exclude_unset=True, exclude_none=True)
    )

    await db.execute(stmt)
    return {"success": True}

@router.get("/{store_id}")
async def get_stores(
    store_id: uuid.UUID,
    store: StoreResponseMini =  Depends(get_store),
    db: AsyncSession = Depends(get_db)
) -> list[StoreResponseMini]:
    # might want to implement redis in the future

    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    sales = (await db.scalars(select(Sale).options(selectinload(Sale.items)).where(
        Sale.store_id == store.store_id, Sale.created_at >= today
    ))).all()

    stocks = (await db.scalars(
        select(Stock).where(
            Stock.store_id == store.store_id, Stock.deleted == False
        )
    )).all()

    
    return {
        **store.model_dump(),
        "stocks": stocks,
        "sales": sales
    }
    
@router.delete('/{store_id}')
async def delete_store(
    request: Request,
    store_id: uuid.UUID,
    store: StoreResponseMini =  Depends(get_store),
    db: AsyncSession = Depends(get_db)
):
    reason = (await request.json()).get("reason", None)
    await db.execute(
        update(Store).where(Store.store_id == store.store_id).values(
            status=StoreStatus.DELETED, delete_reason=reason
        )
    )

    return {"success": True}
