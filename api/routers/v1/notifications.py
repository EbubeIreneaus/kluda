import uuid
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, or_
from models.config import get_db
from models.user import User, UserNotificationSubscription
from models.notification import Notification, NotificationRead
from models.business import Store
from schemas.notification import NotificationScope
from schemas.business import StoreResponseMini
from libs.deps import get_current_user, get_staff_store
from libs.notification_manager import notification_manager

router = APIRouter(prefix="/{store_id}/notifications", tags=["Notifications"])


class PushSubscriptionBody(BaseModel):
    endpoint: str
    keys: dict
    expirationTime: float | None = None


@router.get("")
async def get_store_notifications(
    store_id: uuid.UUID,
    limit: int = 50,
    store: StoreResponseMini = Depends(get_staff_store),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    target_conditions = [
        Notification.scope == NotificationScope.GLOBAL,
        (Notification.scope == NotificationScope.STORE) & (Notification.target_id == store.store_id),
        (Notification.scope == NotificationScope.PERSONAL) & (Notification.target_id == user.user_id),
    ]

    stmt = (
        select(Notification)
        .where(or_(*target_conditions))
        .order_by(Notification.created_at.desc())
        .limit(limit)
    )
    notifications = (await db.scalars(stmt)).all()

    read_ids = set()
    if notifications:
        notif_uuids = [n.notification_id for n in notifications]
        read_stmt = select(NotificationRead.notification_id).where(
            NotificationRead.user_id == user.user_id,
            NotificationRead.notification_id.in_(notif_uuids),
        )
        read_ids = set((await db.scalars(read_stmt)).all())

    return [
        {
            "notification_id": str(n.notification_id),
            "title": n.title,
            "message": n.message,
            "scope": n.scope.value if hasattr(n.scope, "value") else str(n.scope),
            "target_id": str(n.target_id) if n.target_id else None,
            "data": n.data,
            "created_at": n.created_at.isoformat() if n.created_at else None,
            "is_read": n.notification_id in read_ids,
        }
        for n in notifications
    ]


@router.post("/{notification_id}/read")
async def mark_notification_read(
    store_id: uuid.UUID,
    notification_id: uuid.UUID,
    store: StoreResponseMini = Depends(get_staff_store),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.scalar(
        select(NotificationRead).where(
            NotificationRead.user_id == user.user_id,
            NotificationRead.notification_id == notification_id,
        )
    )
    if not existing:
        new_read = NotificationRead(
            user_id=user.user_id,
            notification_id=notification_id,
        )
        db.add(new_read)
        await db.commit()

    return {"success": True}


@router.get("/vapid-public-key")
async def get_vapid_public_key():
    return {"public_key": notification_manager.get_public_key()}


@router.post("/subscribe", status_code=status.HTTP_201_CREATED)
async def subscribe_user(
    store_id: uuid.UUID,
    body: PushSubscriptionBody,
    store: StoreResponseMini = Depends(get_staff_store),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub_data = body.model_dump()
    existing = await db.execute(
        select(UserNotificationSubscription).where(
            UserNotificationSubscription.user_id == user.user_id
        )
    )
    for sub in existing.scalars().all():
        if sub.sub_info.get("endpoint") == body.endpoint:
            return {"success": True, "message": "Already subscribed"}

    new_sub = UserNotificationSubscription(
        user_id=user.user_id,
        sub_info=sub_data
    )
    db.add(new_sub)
    await db.commit()
    return {"success": True, "message": "Subscribed successfully"}


@router.post("/unsubscribe")
async def unsubscribe_user(
    store_id: uuid.UUID,
    body: PushSubscriptionBody,
    store: StoreResponseMini = Depends(get_staff_store),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(UserNotificationSubscription).where(
            UserNotificationSubscription.user_id == user.user_id
        )
    )
    for sub in existing.scalars().all():
        if sub.sub_info.get("endpoint") == body.endpoint:
            await db.delete(sub)
            await db.commit()
            return {"success": True, "message": "Unsubscribed successfully"}

    return {"success": True, "message": "No matching subscription found"}
