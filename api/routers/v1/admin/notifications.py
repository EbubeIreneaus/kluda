import uuid
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.config import get_db
from models.notification import Notification
from models.admin.user import Admin
from schemas.notification import NotificationScope
from schemas.admin.user import AdminPermission
from libs.deps import require_admin_permission, get_admin
from libs.notification_manager import NotificationManager
from libs.audit import record_audit_log


router = APIRouter(prefix="/notifications", tags=["Admin Notifications"])
notif_manager = NotificationManager()


class AdminBroadcastRequest(BaseModel):
    title: str
    message: str
    scope: NotificationScope = NotificationScope.GLOBAL
    target_id: uuid.UUID | None = None
    action_url: str | None = None
    data: dict | None = None


class AdminNotificationResponse(BaseModel):
    id: int
    notification_id: uuid.UUID
    scope: NotificationScope
    target_id: uuid.UUID | None = None
    title: str
    message: str
    data: dict | None = None
    created_at: str

    class Config:
        from_attributes = True


@router.get("")
async def list_notifications(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_admin),
):
    stmt = select(Notification).order_by(Notification.created_at.desc()).limit(limit).offset(offset)
    result = await db.scalars(stmt)
    items = result.all()
    return [
        {
            "id": n.id,
            "notification_id": str(n.notification_id),
            "scope": n.scope.value if hasattr(n.scope, 'value') else str(n.scope),
            "target_id": str(n.target_id) if n.target_id else None,
            "title": n.title,
            "message": n.message,
            "data": n.data,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in items
    ]


@router.post("/broadcast")
async def broadcast_notification(
    payload: AdminBroadcastRequest,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_admin_permission(AdminPermission.MANAGE_ALL)),
):
    notif_data = payload.data or {}
    if payload.action_url:
        notif_data["action_url"] = payload.action_url

    new_notif = Notification(
        scope=payload.scope,
        target_id=payload.target_id,
        title=payload.title,
        message=payload.message,
        data=notif_data,
    )
    db.add(new_notif)
    await db.flush()
    await db.refresh(new_notif)

    if payload.scope == NotificationScope.STORE and payload.target_id:
        await notif_manager.send_to_store(payload.target_id, payload.title, payload.message, notif_data)
    elif payload.scope == NotificationScope.PERSONAL and payload.target_id:
        await notif_manager.send_to_staff(payload.target_id, payload.title, payload.message, notif_data)

    await record_audit_log(
        db=db,
        admin_id=admin.admin_id,
        action="NOTIFICATION_BROADCAST",
        target_type="notification",
        target_id=new_notif.notification_id,
        details={"title": payload.title, "scope": payload.scope.value},
    )

    return {
        "status": "ok",
        "message": "Notification dispatched successfully",
        "notification_id": str(new_notif.notification_id),
    }
