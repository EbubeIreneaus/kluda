from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.config import get_db
from models.faq import FAQ
from models.admin.user import Admin
from schemas.faq import FAQCreate, FAQUpdate, FAQResponse
from schemas.admin.user import AdminPermission
from libs.deps import require_admin_permission
from libs.audit import record_audit_log
from libs.cache import delete_cache_pattern

router = APIRouter(prefix="/faqs", tags=["Admin FAQ Management"])


@router.get("", response_model=List[FAQResponse])
async def list_admin_faqs(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_admin_permission(AdminPermission.MANAGE_SETTINGS)),
):
    """List all FAQs for administration, including unpublished items."""
    query = select(FAQ)
    if category:
        query = query.where(FAQ.category == category)
    query = query.order_by(FAQ.display_order.asc(), FAQ.id.asc())

    result = await db.scalars(query)
    return result.all()


@router.post("", response_model=FAQResponse, status_code=status.HTTP_201_CREATED)
async def create_faq(
    payload: FAQCreate,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_admin_permission(AdminPermission.MANAGE_SETTINGS)),
):
    """Create a new FAQ item and invalidate Redis cache."""
    faq = FAQ(**payload.model_dump())
    db.add(faq)
    await db.commit()
    await db.refresh(faq)

    # Invalidate public FAQ cache
    await delete_cache_pattern("kluda:cache:public_faqs*")

    await record_audit_log(
        db=db,
        actor=admin,
        action="faq:created",
        target=f"faq:{faq.id}",
        meta={"question": faq.question, "category": faq.category},
    )

    return faq


@router.put("/{faq_id}", response_model=FAQResponse)
async def update_faq(
    faq_id: int,
    payload: FAQUpdate,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_admin_permission(AdminPermission.MANAGE_SETTINGS)),
):
    """Update an existing FAQ item and invalidate Redis cache."""
    faq = await db.scalar(select(FAQ).where(FAQ.id == faq_id))
    if not faq:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"FAQ with ID {faq_id} not found",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(faq, key, value)

    await db.commit()
    await db.refresh(faq)

    # Invalidate public FAQ cache
    await delete_cache_pattern("kluda:cache:public_faqs*")

    await record_audit_log(
        db=db,
        actor=admin,
        action="faq:updated",
        target=f"faq:{faq.id}",
        meta=update_data,
    )

    return faq


@router.delete("/{faq_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_faq(
    faq_id: int,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_admin_permission(AdminPermission.MANAGE_SETTINGS)),
):
    """Delete an FAQ item and invalidate Redis cache."""
    faq = await db.scalar(select(FAQ).where(FAQ.id == faq_id))
    if not faq:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"FAQ with ID {faq_id} not found",
        )

    await db.delete(faq)
    await db.commit()

    # Invalidate public FAQ cache
    await delete_cache_pattern("kluda:cache:public_faqs*")

    await record_audit_log(
        db=db,
        actor=admin,
        action="faq:deleted",
        target=f"faq:{faq_id}",
    )

    return None
