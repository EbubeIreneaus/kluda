from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.config import get_db
from models.catalog import CatalogTemplate, CatalogItem
from models.admin.user import Admin
from schemas.catalog import (
    CatalogTemplateCreate,
    CatalogTemplateUpdate,
    CatalogTemplateResponse,
    CatalogItemCreate,
    CatalogItemUpdate,
    CatalogItemResponse,
)
from schemas.admin.user import AdminPermission
from libs.deps import require_admin_permission
from libs.audit import record_audit_log
from libs.cache import delete_cache_pattern

router = APIRouter(prefix="/catalog-templates", tags=["Admin Catalog Management"])


async def invalidate_template_cache(slug: str | None = None):
    """Invalidate Redis caches for templates and items."""
    # Clear all template list caches
    await delete_cache_pattern("catalog:templates:*")
    if slug:
        # Clear single template cache and all item pagination caches for this template
        await delete_cache_pattern(f"catalog:template:{slug}*")
        await delete_cache_pattern(f"{slug}:items:*")
    else:
        await delete_cache_pattern("catalog:template:*")


# =========================================================================
# Template Endpoints
# =========================================================================

@router.post("", response_model=CatalogTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    payload: CatalogTemplateCreate,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_admin_permission(AdminPermission.MANAGE_SETTINGS)),
):
    """Create a new catalog template."""
    clean_slug = payload.slug.strip().lower()
    existing = await db.scalar(
        select(CatalogTemplate).where(CatalogTemplate.slug == clean_slug)
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Template with slug '{clean_slug}' already exists",
        )

    template_data = payload.model_dump()
    template_data["slug"] = clean_slug
    if not template_data.get("icon") or not str(template_data["icon"]).strip():
        template_data["icon"] = "package"
    else:
        template_data["icon"] = str(template_data["icon"]).strip().lower()
    template = CatalogTemplate(**template_data)
    db.add(template)
    await db.commit()
    await db.refresh(template)

    await invalidate_template_cache(template.slug)

    await record_audit_log(
        db=db,
        admin_id=admin.admin_id,
        action="catalog_template:created",
        target_type="catalog_template",
        details={"name": template.name, "slug": template.slug},
    )

    return template


@router.put("/{template_id}", response_model=CatalogTemplateResponse)
async def update_template(
    template_id: int,
    payload: CatalogTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_admin_permission(AdminPermission.MANAGE_SETTINGS)),
):
    """Update an existing catalog template."""
    template = await db.scalar(
        select(CatalogTemplate).where(CatalogTemplate.id == template_id)
    )
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Catalog template #{template_id} not found",
        )

    old_slug = template.slug
    update_data = payload.model_dump(exclude_unset=True)

    if "slug" in update_data and update_data["slug"]:
        new_slug = update_data["slug"].strip().lower()
        if new_slug != old_slug:
            existing = await db.scalar(
                select(CatalogTemplate).where(CatalogTemplate.slug == new_slug)
            )
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Template with slug '{new_slug}' already exists",
                )
            update_data["slug"] = new_slug

    if "icon" in update_data:
        if not update_data["icon"] or not str(update_data["icon"]).strip():
            update_data["icon"] = "package"
        else:
            update_data["icon"] = str(update_data["icon"]).strip().lower()

    for key, value in update_data.items():
        setattr(template, key, value)

    await db.commit()
    await db.refresh(template)

    await invalidate_template_cache(old_slug)
    if template.slug != old_slug:
        await invalidate_template_cache(template.slug)

    await record_audit_log(
        db=db,
        admin_id=admin.admin_id,
        action="catalog_template:updated",
        target_type="catalog_template",
        details={"name": template.name, "slug": template.slug},
    )

    return template


@router.delete("/{template_id}", status_code=status.HTTP_200_OK)
async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_admin_permission(AdminPermission.MANAGE_SETTINGS)),
):
    """Delete a catalog template and all its associated items."""
    template = await db.scalar(
        select(CatalogTemplate).where(CatalogTemplate.id == template_id)
    )
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Catalog template #{template_id} not found",
        )

    slug = template.slug
    await db.delete(template)
    await db.commit()

    await invalidate_template_cache(slug)

    await record_audit_log(
        db=db,
        admin_id=admin.admin_id,
        action="catalog_template:deleted",
        target_type="catalog_template",
        details={"name": template.name, "slug": slug},
    )

    return {"message": f"Catalog template '{template.name}' successfully deleted"}


# =========================================================================
# Item Endpoints
# =========================================================================

@router.post("/{template_id}/items", response_model=CatalogItemResponse, status_code=status.HTTP_201_CREATED)
async def add_item_to_template(
    template_id: int,
    payload: CatalogItemCreate,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_admin_permission(AdminPermission.MANAGE_SETTINGS)),
):
    """Add a new product item to a catalog template."""
    template = await db.scalar(
        select(CatalogTemplate).where(CatalogTemplate.id == template_id)
    )
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Catalog template #{template_id} not found",
        )

    clean_barcode = payload.barcode.strip() if payload.barcode and payload.barcode.strip() else None

    # Check for duplicate barcode in same template
    if clean_barcode:
        duplicate = await db.scalar(
            select(CatalogItem).where(
                CatalogItem.template_id == template_id,
                CatalogItem.barcode == clean_barcode,
            )
        )
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"An item with barcode '{clean_barcode}' already exists in this template",
            )

    item_data = payload.model_dump()
    item_data["template_id"] = template_id
    item_data["barcode"] = clean_barcode

    item = CatalogItem(**item_data)
    db.add(item)
    await db.commit()
    await db.refresh(item)

    # Invalidate items and template counts
    await invalidate_template_cache(template.slug)

    await record_audit_log(
        db=db,
        admin_id=admin.admin_id,
        action="catalog_item:created",
        target_type="catalog_item",
        details={"name": item.name, "barcode": item.barcode, "template": template.slug},
    )

    return item


@router.put("/items/{item_id}", response_model=CatalogItemResponse)
async def update_item(
    item_id: int,
    payload: CatalogItemUpdate,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_admin_permission(AdminPermission.MANAGE_SETTINGS)),
):
    """Update a specific catalog item."""
    item = await db.scalar(
        select(CatalogItem).where(CatalogItem.id == item_id)
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Catalog item #{item_id} not found",
        )

    template = await db.scalar(
        select(CatalogTemplate).where(CatalogTemplate.id == item.template_id)
    )

    update_data = payload.model_dump(exclude_unset=True)

    if "barcode" in update_data and update_data["barcode"]:
        clean_barcode = update_data["barcode"].strip()
        if clean_barcode != item.barcode:
            duplicate = await db.scalar(
                select(CatalogItem).where(
                    CatalogItem.template_id == item.template_id,
                    CatalogItem.barcode == clean_barcode,
                    CatalogItem.id != item_id,
                )
            )
            if duplicate:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"An item with barcode '{clean_barcode}' already exists in this template",
                )
            update_data["barcode"] = clean_barcode

    for key, value in update_data.items():
        setattr(item, key, value)

    await db.commit()
    await db.refresh(item)

    if template:
        await invalidate_template_cache(template.slug)

    await record_audit_log(
        db=db,
        admin_id=admin.admin_id,
        action="catalog_item:updated",
        target_type="catalog_item",
        details={"name": item.name, "barcode": item.barcode},
    )

    return item


@router.delete("/items/{item_id}", status_code=status.HTTP_200_OK)
async def delete_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_admin_permission(AdminPermission.MANAGE_SETTINGS)),
):
    """Delete a specific catalog item."""
    item = await db.scalar(
        select(CatalogItem).where(CatalogItem.id == item_id)
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Catalog item #{item_id} not found",
        )

    template = await db.scalar(
        select(CatalogTemplate).where(CatalogTemplate.id == item.template_id)
    )

    name = item.name
    await db.delete(item)
    await db.commit()

    if template:
        await invalidate_template_cache(template.slug)

    await record_audit_log(
        db=db,
        admin_id=admin.admin_id,
        action="catalog_item:deleted",
        target_type="catalog_item",
        details={"name": name},
    )

    return {"message": f"Catalog item '{name}' deleted"}
