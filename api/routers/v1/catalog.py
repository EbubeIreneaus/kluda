import math
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from models.config import get_db
from models.catalog import CatalogTemplate, CatalogItem
from models.stock import Stock
from schemas.catalog import (
    CatalogTemplateResponse,
    CatalogItemResponse,
    PaginatedCatalogItemsResponse,
)
from libs.cache import get_cache, set_cache

router = APIRouter(prefix="/catalog-templates", tags=["Catalog Templates (Public)"])

CACHE_TTL_TEMPLATES = 3600  # 1 hour
CACHE_TTL_ITEMS = 3600      # 1 hour


@router.get("", response_model=List[CatalogTemplateResponse])
async def list_catalog_templates(
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """
    List all catalog templates with item counts and import counts.
    Cached in Redis using key 'catalog:templates:all'.
    """
    cache_key = f"catalog:templates:all:{include_inactive}"
    cached_data = await get_cache(cache_key)
    if cached_data is not None:
        return cached_data

    # Query templates with count of items
    stmt = (
        select(
            CatalogTemplate,
            func.count(CatalogItem.id).label("total_items")
        )
        .outerjoin(CatalogItem, CatalogItem.template_id == CatalogTemplate.id)
        .group_by(CatalogTemplate.id)
        .order_by(CatalogTemplate.sort_order.asc(), CatalogTemplate.id.asc())
    )

    if not include_inactive:
        stmt = stmt.where(CatalogTemplate.is_active == True)

    results = await db.execute(stmt)
    rows = results.all()

    response_list = []
    for template, total_items in rows:
        template_dict = {
            "id": template.id,
            "name": template.name,
            "slug": template.slug,
            "description": template.description,
            "icon": template.icon or "package",
            "is_active": template.is_active,
            "sort_order": template.sort_order,
            "total_imports": template.total_imports or 0,
            "total_items": total_items or 0,
            "created_at": template.created_at.isoformat() if template.created_at else None,
            "updated_at": template.updated_at.isoformat() if template.updated_at else None,
        }
        response_list.append(template_dict)

    await set_cache(cache_key, response_list, expire_seconds=CACHE_TTL_TEMPLATES)
    return response_list


@router.get("/lookup")
async def lookup_product_by_barcode(
    barcode: str = Query(..., min_length=2, description="Barcode or SKU to lookup"),
    db: AsyncSession = Depends(get_db),
):
    """
    Lookup product metadata by barcode for fast Scan-to-Add.
    1. First searches Kluda verified master catalog.
    2. If not found and barcode is standard manufacturer GTIN (8-14 digits),
       searches community products for matching name & unit.
    """
    clean_barcode = barcode.strip()
    if not clean_barcode:
        return {"found": False}

    cache_key = f"catalog:lookup:{clean_barcode}"
    cached_data = await get_cache(cache_key)
    if cached_data is not None:
        return cached_data

    # 1. Search Kluda Verified Master Catalog
    catalog_stmt = (
        select(CatalogItem)
        .where(
            CatalogItem.barcode == clean_barcode,
            CatalogItem.is_active == True,
        )
        .order_by(CatalogItem.id.asc())
        .limit(1)
    )
    catalog_item = await db.scalar(catalog_stmt)
    if catalog_item:
        result = {
            "found": True,
            "source": "catalog",
            "name": catalog_item.name,
            "barcode": catalog_item.barcode,
            "category": catalog_item.category,
            "suggested_price": catalog_item.suggested_price,  # in kobo
            "cost_price": catalog_item.cost_price,            # in kobo
            "unit_in": catalog_item.unit_in,
            "description": catalog_item.description,
        }
        await set_cache(cache_key, result, expire_seconds=CACHE_TTL_ITEMS)
        return result

    # 2. Search Community Products (stocks) if barcode is a valid manufacturer GTIN
    if clean_barcode.isdigit() and len(clean_barcode) in (8, 12, 13, 14):
        stock_stmt = (
            select(Stock)
            .where(
                Stock.barcode_id == clean_barcode,
                Stock.deleted == False,
                Stock.name.isnot(None),
            )
            .order_by(Stock.id.desc())
            .limit(1)
        )
        stock_item = await db.scalar(stock_stmt)
        if stock_item and stock_item.name:
            result = {
                "found": True,
                "source": "community",
                "name": stock_item.name.strip(),
                "barcode": stock_item.barcode_id,
                "category": "General",
                "suggested_price": stock_item.unit_price or 0,  # community retail price in kobo
                "unit_in": stock_item.unit_in or "piece",
                "description": stock_item.description or None,
            }
            await set_cache(cache_key, result, expire_seconds=CACHE_TTL_ITEMS)
            return result

    # 3. Not found
    result = {"found": False}
    await set_cache(cache_key, result, expire_seconds=300)
    return result


@router.get("/{slug}", response_model=CatalogTemplateResponse)
async def get_catalog_template(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get single catalog template by slug.
    Cached in Redis using key 'catalog:template:{slug}'.
    """
    cache_key = f"catalog:template:{slug}"
    cached_data = await get_cache(cache_key)
    if cached_data is not None:
        return cached_data

    stmt = (
        select(
            CatalogTemplate,
            func.count(CatalogItem.id).label("total_items")
        )
        .outerjoin(CatalogItem, CatalogItem.template_id == CatalogTemplate.id)
        .where(CatalogTemplate.slug == slug)
        .group_by(CatalogTemplate.id)
    )

    result = await db.execute(stmt)
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Catalog template '{slug}' not found",
        )

    template, total_items = row
    template_dict = {
        "id": template.id,
        "name": template.name,
        "slug": template.slug,
        "description": template.description,
        "icon": template.icon or "package",
        "is_active": template.is_active,
        "sort_order": template.sort_order,
        "total_imports": template.total_imports or 0,
        "total_items": total_items or 0,
        "created_at": template.created_at.isoformat() if template.created_at else None,
        "updated_at": template.updated_at.isoformat() if template.updated_at else None,
    }

    await set_cache(cache_key, template_dict, expire_seconds=CACHE_TTL_TEMPLATES)
    return template_dict


@router.get("/{slug}/items", response_model=PaginatedCatalogItemsResponse)
async def list_catalog_template_items(
    slug: str,
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(default=None, description="Search by product name, barcode, or category"),
    has_barcode: Optional[bool] = Query(default=None, description="Filter by barcode presence: true for with barcode, false for without barcode"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get paginated items for a catalog template.
    Cached in Redis using key '{slug}:items:{page}:{page_size}:{search}:{has_barcode}'.
    """
    clean_search = search.strip().lower() if search and search.strip() else ""
    barcode_filter_key = "all" if has_barcode is None else ("with" if has_barcode else "none")
    cache_key = f"{slug}:items:{page}:{page_size}:{clean_search}:{barcode_filter_key}"

    cached_data = await get_cache(cache_key)
    if cached_data is not None:
        return cached_data

    # Verify template exists
    template = await db.scalar(
        select(CatalogTemplate).where(CatalogTemplate.slug == slug)
    )
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Catalog template '{slug}' not found",
        )

    # Build items query
    base_query = select(CatalogItem).where(
        CatalogItem.template_id == template.id,
        CatalogItem.is_active == True,
    )

    if clean_search:
        term = f"%{clean_search}%"
        base_query = base_query.where(
            or_(
                CatalogItem.name.ilike(term),
                CatalogItem.barcode.ilike(term),
                CatalogItem.category.ilike(term),
            )
        )

    if has_barcode is True:
        base_query = base_query.where(
            CatalogItem.barcode.isnot(None),
            CatalogItem.barcode != "",
        )
    elif has_barcode is False:
        base_query = base_query.where(
            or_(
                CatalogItem.barcode.is_(None),
                CatalogItem.barcode == "",
            )
        )

    # Count total
    count_stmt = select(func.count()).select_from(base_query.subquery())
    total = (await db.scalar(count_stmt)) or 0

    # Paginate
    offset = (page - 1) * page_size
    items_stmt = base_query.order_by(CatalogItem.id.asc()).offset(offset).limit(page_size)
    items_result = await db.scalars(items_stmt)
    items = items_result.all()

    total_pages = math.ceil(total / page_size) if total > 0 else 1

    response_data = {
        "items": [
            {
                "id": item.id,
                "template_id": item.template_id,
                "name": item.name,
                "barcode": item.barcode,
                "category": item.category,
                "suggested_price": item.suggested_price,
                "cost_price": item.cost_price,
                "unit_in": item.unit_in,
                "description": item.description,
                "is_active": item.is_active,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "updated_at": item.updated_at.isoformat() if item.updated_at else None,
            }
            for item in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }

    await set_cache(cache_key, response_data, expire_seconds=CACHE_TTL_ITEMS)
    return response_data


# =========================================================================
# Merchant Import Action
# =========================================================================

import re
import uuid
from datetime import datetime, timezone
from fastapi import Request
from models.business import Store
from models.user import User
from models.admin.plan import Plan
from models.subscription import UserSubscription
from models.stock import Stock
from schemas.user import StaffPermission
from schemas.business import StoreResponseMini
from libs.deps import get_staff_store, require_permission
from libs.audit import record_store_audit
from libs.security import get_client_ip
from libs.cache import delete_cache_pattern


def _slugify(text: str, prefix: str = "") -> str:
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    text = re.sub(r"[-\s]+", "-", text)
    return f"{prefix}-{text}" if prefix else text


@router.post("/{slug}/import")
async def import_catalog_template(
    slug: str,
    store_id: uuid.UUID,
    request: Request,
    store: StoreResponseMini = Depends(get_staff_store),
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_permission(StaffPermission.CREATE_PRODUCT)),
):
    """
    1-Click Import: Copies products from a starter pack into the merchant's store.
    Safely skips existing products by barcode and name to avoid duplicate collisions.
    """
    # 1. Fetch template
    template = await db.scalar(
        select(CatalogTemplate).where(
            CatalogTemplate.slug == slug,
            CatalogTemplate.is_active == True,
        )
    )
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Catalog template '{slug}' not found or inactive",
        )

    # 2. Fetch template items
    items = (
        await db.scalars(
            select(CatalogItem).where(
                CatalogItem.template_id == template.id,
                CatalogItem.is_active == True,
            ).order_by(CatalogItem.id.asc())
        )
    ).all()

    if not items:
        return {
            "imported": 0,
            "skipped": 0,
            "message": "No active products found in this starter pack to import.",
        }

    # 3. Check store subscription limit
    db_store = await db.scalar(select(Store).where(Store.store_id == store.store_id))
    owner_user_id = db_store.user_id if db_store else None
    owner = (
        await db.scalar(select(User).where(User.user_id == owner_user_id))
        if owner_user_id
        else None
    )
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

    # 4. Fetch existing products for deduplication
    existing_stocks = (
        await db.scalars(
            select(Stock).where(
                Stock.store_id == store.store_id,
                Stock.deleted == False,
            )
        )
    ).all()

    existing_barcodes = {
        s.barcode_id.strip()
        for s in existing_stocks
        if s.barcode_id and s.barcode_id.strip()
    }
    existing_names = {s.name.strip().lower() for s in existing_stocks if s.name}
    existing_slugs = {s.slug for s in existing_stocks if s.slug}
    current_count = len(existing_stocks)

    # 5. Build new Stock entries
    new_stocks: list[Stock] = []
    skipped = 0
    prefix = store.name[:4].lower().replace(" ", "") if store.name else "st"

    for it in items:
        # Check barcode duplicate
        clean_barcode = it.barcode.strip() if it.barcode and it.barcode.strip() else None
        if clean_barcode and clean_barcode in existing_barcodes:
            skipped += 1
            continue

        # Check name duplicate
        if it.name.strip().lower() in existing_names:
            skipped += 1
            continue

        # Check product limit
        if product_limit and product_limit > 0 and (current_count + len(new_stocks)) >= product_limit:
            # Hit product limit for current plan
            break

        # Generate unique slug
        base_slug = _slugify(it.name, prefix=prefix)
        item_slug = base_slug
        counter = 1
        while item_slug in existing_slugs:
            item_slug = f"{base_slug}-{counter}"
            counter += 1

        existing_slugs.add(item_slug)
        if clean_barcode:
            existing_barcodes.add(clean_barcode)
        existing_names.add(it.name.strip().lower())

        new_stock = Stock(
            name=it.name,
            slug=item_slug,
            store_id=store.store_id,
            barcode_id=clean_barcode,
            unit_price=it.suggested_price,
            cost_price=it.cost_price,
            sku=None,
            quantities=0,
            unit_in=it.unit_in,
            max_discount=0,
            description=it.description,
            deleted=False,
        )
        new_stocks.append(new_stock)

    if not new_stocks:
        return {
            "imported": 0,
            "skipped": skipped,
            "message": "All products in this pack already exist in your store.",
        }

    # 6. Bulk insert & update template metrics
    db.add_all(new_stocks)
    template.total_imports = (template.total_imports or 0) + 1
    await db.commit()

    # 7. Invalidate Redis template caches
    await delete_cache_pattern("catalog:templates:*")
    await delete_cache_pattern(f"catalog:template:{slug}*")

    # 8. Record store audit log
    await record_store_audit(
        db=db,
        store_id=store.store_id,
        action="catalog.import",
        target_type="catalog_template",
        actor=actor,
        target_id=str(template.id),
        target_name=template.name,
        details={
            "imported_count": len(new_stocks),
            "skipped_count": skipped,
            "template_slug": template.slug,
        },
        ip_address=get_client_ip(request),
    )

    return {
        "imported": len(new_stocks),
        "skipped": skipped,
        "message": f"Successfully imported {len(new_stocks)} products from {template.name}!",
    }

