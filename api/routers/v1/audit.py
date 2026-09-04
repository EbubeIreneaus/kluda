from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from models.config import get_db
from models.store_audit import StoreAuditLog
from models.user import User
from schemas.audit import StoreAuditLogPaginationResponse, StoreAuditLogResponse
from schemas.user import StaffPermission
from schemas.business import StoreResponseMini
from libs.deps import require_permission, get_staff_store
import uuid

router = APIRouter(prefix="/{store_id}/audit-logs", tags=["Store Audit Logs"])


@router.get("", response_model=StoreAuditLogPaginationResponse)
@router.get("/", response_model=StoreAuditLogPaginationResponse, include_in_schema=False)
async def get_store_audit_logs(
    store_id: uuid.UUID,
    action: str | None = Query(None),
    target_type: str | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    store: StoreResponseMini = Depends(get_staff_store),
    user: User = Depends(require_permission(StaffPermission.VIEW_AUDIT_LOG)),
):
    base_filter = [StoreAuditLog.store_id == store_id]

    if action:
        base_filter.append(StoreAuditLog.action == action)
    if target_type:
        base_filter.append(StoreAuditLog.target_type == target_type)
    if search and search.strip():
        search_pattern = f"%{search.strip()}%"
        base_filter.append(
            or_(
                StoreAuditLog.target_name.ilike(search_pattern),
                StoreAuditLog.actor_name.ilike(search_pattern),
                StoreAuditLog.actor_email.ilike(search_pattern),
                StoreAuditLog.action.ilike(search_pattern),
                StoreAuditLog.target_id.ilike(search_pattern),
            )
        )

    count_stmt = select(func.count()).select_from(StoreAuditLog).where(*base_filter)
    total = await db.scalar(count_stmt) or 0

    stmt = (
        select(StoreAuditLog)
        .where(*base_filter)
        .order_by(StoreAuditLog.created_at.desc(), StoreAuditLog.id.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.scalars(stmt)
    items = result.all()

    return StoreAuditLogPaginationResponse(
        items=[StoreAuditLogResponse.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )
