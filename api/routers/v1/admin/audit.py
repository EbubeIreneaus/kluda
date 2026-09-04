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
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate


router = APIRouter(prefix="/audit", tags=["Admin Audit Logs"])


def _log_to_response(log: AdminAuditLog) -> AdminAuditLogResponse:
    admin_name = log.admin.fullname if log.admin else None
    admin_email = (
        log.admin.company_email or log.admin.personal_email if log.admin else None
    )
    return AdminAuditLogResponse(
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


@router.get("", response_model=list[AdminAuditLogResponse])
async def list_audit_logs_preview(
    action: str | None = Query(None),
    target_type: str | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_admin_permission(AdminPermission.VIEW_AUDIT_LOGS)),
):
    """Return a small preview of the most recent audit events (used by settings page)."""
    stmt = (
        select(AdminAuditLog)
        .options(selectinload(AdminAuditLog.admin))
        .order_by(AdminAuditLog.created_at.desc())
        .limit(limit)
    )
    if action:
        stmt = stmt.where(AdminAuditLog.action == action)
    if target_type:
        stmt = stmt.where(AdminAuditLog.target_type == target_type)

    result = await db.scalars(stmt)
    return [_log_to_response(log) for log in result.all()]


@router.get("/paginated", response_model=Page[AdminAuditLogResponse])
async def list_audit_logs_paginated(
    action: str | None = Query(None),
    target_type: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_admin_permission(AdminPermission.VIEW_AUDIT_LOGS)),
):
    """Fully paginated audit log endpoint for the full-screen audit viewer."""
    stmt = (
        select(AdminAuditLog)
        .options(selectinload(AdminAuditLog.admin))
        .order_by(AdminAuditLog.created_at.desc())
    )
    if action:
        stmt = stmt.where(AdminAuditLog.action == action)
    if target_type:
        stmt = stmt.where(AdminAuditLog.target_type == target_type)

    return await paginate(db, stmt, transformer=lambda items: [_log_to_response(log) for log in items])