from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.config import get_db
from models.admin.audit import AdminAuditLog
from models.admin.user import Admin
from schemas.admin.audit import AdminAuditLogResponse
from schemas.admin.user import AdminPermission
from libs.deps import require_admin_permission


router = APIRouter(prefix="/audit", tags=["Admin Audit Logs"])


@router.get("", response_model=list[AdminAuditLogResponse])
async def list_audit_logs(
    action: str | None = Query(None),
    target_type: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_admin_permission(AdminPermission.VIEW_AUDIT_LOGS)),
):
    stmt = select(AdminAuditLog)
    if action:
        stmt = stmt.where(AdminAuditLog.action == action)
    if target_type:
        stmt = stmt.where(AdminAuditLog.target_type == target_type)

    stmt = stmt.order_by(AdminAuditLog.created_at.desc()).limit(limit).offset(offset)
    result = await db.scalars(stmt)
    return result.all()
