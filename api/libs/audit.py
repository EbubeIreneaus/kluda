from sqlalchemy.ext.asyncio import AsyncSession
from models.admin.audit import AdminAuditLog
from models.store_audit import StoreAuditLog
from models.user import User
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


async def record_store_audit(
    db: AsyncSession,
    store_id: uuid.UUID,
    action: str,
    target_type: str,
    actor: User | None = None,
    actor_id: uuid.UUID | None = None,
    actor_name: str | None = None,
    actor_email: str | None = None,
    actor_role: str | None = None,
    target_id: str | None = None,
    target_name: str | None = None,
    details: dict | None = None,
    ip_address: str | None = None,
) -> StoreAuditLog:
    if actor is not None:
        if actor_id is None:
            actor_id = getattr(actor, "user_id", None)
        if actor_name is None:
            actor_name = getattr(actor, "fullname", None)
        if actor_email is None:
            actor_email = getattr(actor, "email", None)

    log_entry = StoreAuditLog(
        store_id=store_id,
        actor_id=actor_id,
        actor_name=actor_name,
        actor_email=actor_email,
        actor_role=actor_role,
        action=action,
        target_type=target_type,
        target_id=str(target_id) if target_id is not None else None,
        target_name=target_name,
        details=details,
        ip_address=ip_address,
    )
    db.add(log_entry)
    await db.flush()
    return log_entry
