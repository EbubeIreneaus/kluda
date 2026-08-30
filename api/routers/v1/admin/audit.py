from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
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
    stmt = select(AdminAuditLog).options(selectinload(AdminAuditLog.admin))
    if action:
        stmt = stmt.where(AdminAuditLog.action == action)
    if target_type:
        stmt = stmt.where(AdminAuditLog.target_type == target_type)

    stmt = stmt.order_by(AdminAuditLog.created_at.desc()).limit(limit).offset(offset)
    result = await db.scalars(stmt)
    logs = result.all()

    output = []
    for log in logs:
        admin_name = log.admin.fullname if log.admin else None
        admin_email = log.admin.company_email or log.admin.personal_email if log.admin else None
        output.append(
            AdminAuditLogResponse(
                id=log.id,
                log_id=log.log_id,
                admin_id=log.admin_id,
                admin_name=admin_name,
                admin_email=admin_email,
                action=log.action,
                target_type=log.target_type,
                target_id=log.target_id,
                details=log.details,
                ip_address=log.ip_address,
                created_at=log.created_at,
            )
        )
    return output
