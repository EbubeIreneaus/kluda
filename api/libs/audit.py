from sqlalchemy.ext.asyncio import AsyncSession
from models.admin.audit import AdminAuditLog
import uuid


async def record_audit_log(
    db: AsyncSession,
    admin_id: uuid.UUID | None,
    action: str,
    target_type: str,
    target_id: uuid.UUID | None = None,
    details: dict | None = None,
    ip_address: str | None = None,
) -> AdminAuditLog:
    log_entry = AdminAuditLog(
        admin_id=admin_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
        ip_address=ip_address,
    )
    db.add(log_entry)
    await db.flush()
    return log_entry
