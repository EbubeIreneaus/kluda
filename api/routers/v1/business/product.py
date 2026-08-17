from schemas.business import StoreResponseMini
import re
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from models.config import get_db
from models.stock import Stock
from schemas.stock import StockCreate, StockUpdate, StockResponse
from schemas.user import StaffPermission
from models.user import Staff
from libs.deps import require_permission, get_staff, get_staff_store
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


@router.post("/", response_model=StockResponse, status_code=status.HTTP_201_CREATED)
async def create_stock(
    stock_data: StockCreate,
    store_id: uuid.UUID,
    store: StoreResponseMini = Depends(get_staff_store),
    db: AsyncSession = Depends(get_db),
    staff_id: str = Query(default="unknown", description="Staff ID for WS broadcast exclusion"),
    _: Staff = Depends(require_permission(StaffPermission.MANAGE_PRODUCT)),
):
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

    await db.commit()
    await db.refresh(new_stock)
    await ws_manager.broadcast(
        {"event": "add_product", "data": StockResponse.model_validate(new_stock).model_dump(mode="json")},
        exclude_staff_id=staff_id,
    )
    return new_stock


@router.get("/", response_model=list[StockResponse])
async def get_stocks(
    store_id: uuid.UUID,
    store: StoreResponseMini = Depends(get_staff_store),
    search: str | None = Query(
        None, description="Search products by name, description, SKU or barcode"
    ),
    db: AsyncSession = Depends(get_db),
    _: Staff = Depends(require_permission(StaffPermission.VIEW_PRODUCT)),
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
    _: Staff = Depends(require_permission(StaffPermission.VIEW_PRODUCT)),
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
    store: StoreResponseMini = Depends(get_staff_store),
    db: AsyncSession = Depends(get_db),
    staff_id: str = Query(default="unknown", description="Staff ID for WS broadcast exclusion"),
    _: Staff = Depends(require_permission(StaffPermission.MANAGE_PRODUCT)),
):
    res = await db.execute(select(Stock).where(Stock.slug == slug, Stock.store_id == store.store_id))
    stock = res.scalar_one_or_none()
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with slug '{slug}' not found",
        )

    # Check barcode uniqueness if updating barcode
    if update_data.barcode_id and update_data.barcode_id.strip():
        existing_barcode = await db.execute(
            select(Stock).where(
                Stock.barcode_id == update_data.barcode_id.strip(),
                Stock.slug != slug,
                Stock.deleted == False,
                Stock.store_id == store.store_id
            )
        )
        if existing_barcode.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A product with barcode '{update_data.barcode_id}' already exists",
            )

    values = update_data.model_dump(exclude_unset=True, exclude_none=True)
    if values:
        await db.execute(update(Stock).values(**values).where(Stock.slug == slug))

    await db.commit()
    await db.refresh(stock)
    await ws_manager.broadcast(
        {"event": "update_product", "data": StockResponse.model_validate(stock).model_dump(mode="json")},
        exclude_staff_id=staff_id,
    )
    return {"success": True}


@router.delete("/{slug}")
async def delete_stock(
    slug: str,
    store_id: uuid.UUID,
    store: StoreResponseMini = Depends(get_staff_store),
    db: AsyncSession = Depends(get_db),
    staff_id: str = Query(default="unknown", description="Staff ID for WS broadcast exclusion"),
    _: Staff = Depends(require_permission(StaffPermission.MANAGE_PRODUCT)),
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
    await db.commit()
    await ws_manager.broadcast(
        {"event": "delete_product", "data": {"slug": slug}},
        exclude_staff_id=staff_id,
    )
    return {"message": f"Product '{slug}' deleted successfully"}
