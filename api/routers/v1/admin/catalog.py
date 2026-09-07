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
from libs.cache import delete_cache, delete_cache_pattern

router = APIRouter(prefix="/catalog-templates", tags=["Admin Catalog Management"])


async def invalidate_template_cache(
    slug: str | None = None,
    barcodes: list[str | None] | str | None = None,
):
    """Invalidate Redis caches for templates, items, and barcode lookups."""
    # Clear all template list caches
    await delete_cache_pattern("catalog:templates:*")

    if slug:
        # Clear single template cache and all item pagination caches for this template
        await delete_cache_pattern(f"catalog:template:{slug}*")
        await delete_cache_pattern(f"catalog:items:{slug}:*")
        await delete_cache_pattern(f"{slug}:items:*")
    else:
        # Clear all single template caches and all item pagination caches
        await delete_cache_pattern("catalog:template:*")
        await delete_cache_pattern("catalog:items:*")
        await delete_cache_pattern("*:items:*")

    # Invalidate specific barcode lookups or all lookups
    if barcodes is not None:
        bc_list = [barcodes] if isinstance(barcodes, str) else barcodes
        keys_to_delete = []
        for bc in bc_list:
            if bc:
                clean_bc = str(bc).strip()
                if clean_bc:
                    keys_to_delete.append(f"catalog:lookup:{clean_bc}")
        if keys_to_delete:
            await delete_cache(*keys_to_delete)
    elif slug is None:
        # If no slug is specified (global cache invalidation), clear all barcode lookup caches as well
        await delete_cache_pattern("catalog:lookup:*")


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

    # If template deactivated, also invalidate barcode lookups for all its items
    if "is_active" in update_data and update_data["is_active"] is False:
        item_barcodes = (
            await db.scalars(
                select(CatalogItem.barcode).where(
                    CatalogItem.template_id == template_id,
                    CatalogItem.barcode.isnot(None),
                )
            )
        ).all()
        await invalidate_template_cache(old_slug, barcodes=list(item_barcodes))
    else:
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

    # Collect item barcodes to invalidate lookup caches
    item_barcodes = (
        await db.scalars(
            select(CatalogItem.barcode).where(
                CatalogItem.template_id == template_id,
                CatalogItem.barcode.isnot(None),
            )
        )
    ).all()

    await db.delete(template)
    await db.commit()

    await invalidate_template_cache(slug, barcodes=list(item_barcodes))

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
    reassign_barcode = bool(payload.reassign_barcode is True)

    # Check for duplicate barcode in same template
    duplicate = None
    if clean_barcode:
        duplicate = await db.scalar(
            select(CatalogItem).where(
                CatalogItem.template_id == template_id,
                CatalogItem.barcode == clean_barcode,
            )
        )
        if duplicate:
            if not reassign_barcode:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": "BARCODE_CONFLICT",
                        "message": f"Barcode '{clean_barcode}' already exists on '{duplicate.name}'",
                        "existing_item_id": duplicate.id,
                        "existing_item_name": duplicate.name,
                        "barcode": clean_barcode,
                    },
                )
            else:
                duplicate.barcode = None

    item_data = payload.model_dump()
    item_data.pop("reassign_barcode", None)
    item_data["template_id"] = template_id
    item_data["barcode"] = clean_barcode

    item = CatalogItem(**item_data)
    db.add(item)
    await db.commit()
    await db.refresh(item)

    # Invalidate items, template counts, and new item barcode lookup cache
    await invalidate_template_cache(template.slug, barcodes=item.barcode)

    await record_audit_log(
        db=db,
        admin_id=admin.admin_id,
        action="catalog_item:created",
        target_type="catalog_item",
        details={"name": item.name, "barcode": item.barcode, "template": template.slug},
    )

    if duplicate and reassign_barcode:
        await record_audit_log(
            db=db,
            admin_id=admin.admin_id,
            action="catalog_item:barcode_reassigned",
            target_type="catalog_item",
            details={
                "previous_item_id": duplicate.id,
                "previous_item_name": duplicate.name,
                "barcode": clean_barcode,
                "new_item_name": item.name,
            },
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

    old_barcode = item.barcode
    reassign_barcode = bool(payload.reassign_barcode is True)
    update_data = payload.model_dump(exclude_unset=True)
    update_data.pop("reassign_barcode", None)

    reassigned_duplicate = None
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
                if not reassign_barcode:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail={
                            "code": "BARCODE_CONFLICT",
                            "message": f"Barcode '{clean_barcode}' already exists on '{duplicate.name}'",
                            "existing_item_id": duplicate.id,
                            "existing_item_name": duplicate.name,
                            "barcode": clean_barcode,
                        },
                    )
                else:
                    duplicate.barcode = None
                    reassigned_duplicate = duplicate
            update_data["barcode"] = clean_barcode

    for key, value in update_data.items():
        setattr(item, key, value)

    await db.commit()
    await db.refresh(item)

    if template:
        barcodes_to_clear = [b for b in [old_barcode, item.barcode] if b]
        await invalidate_template_cache(template.slug, barcodes=barcodes_to_clear)

    await record_audit_log(
        db=db,
        admin_id=admin.admin_id,
        action="catalog_item:updated",
        target_type="catalog_item",
        details={"name": item.name, "barcode": item.barcode},
    )

    if reassigned_duplicate:
        await record_audit_log(
            db=db,
            admin_id=admin.admin_id,
            action="catalog_item:barcode_reassigned",
            target_type="catalog_item",
            details={
                "previous_item_id": reassigned_duplicate.id,
                "previous_item_name": reassigned_duplicate.name,
                "barcode": item.barcode,
                "new_item_name": item.name,
            },
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
    old_barcode = item.barcode
    await db.delete(item)
    await db.commit()

    if template:
        await invalidate_template_cache(template.slug, barcodes=old_barcode)

    await record_audit_log(
        db=db,
        admin_id=admin.admin_id,
        action="catalog_item:deleted",
        target_type="catalog_item",
        details={"name": name},
    )

    return {"message": f"Catalog item '{name}' deleted"}
