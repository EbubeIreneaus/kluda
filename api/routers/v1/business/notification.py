import uuid
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, or_
from models.config import get_db
from models.user import Staff, StaffNotificationSubscription, UserNotificationSubscription
from models.notification import Notification, NotificationRead
from models.business import Store
from schemas.notification import NotificationScope
from schemas.business import StoreResponseMini
from libs.deps import get_staff, get_staff_store
from libs.notification_manager import notification_manager

router = APIRouter(prefix="/{store_id}/notifications", tags=["Staff Notifications"])


class PushSubscriptionBody(BaseModel):
    endpoint: str
    keys: dict
    expirationTime: float | None = None


@router.get("")
async def get_store_notifications(
    store_id: uuid.UUID,
    limit: int = 50,
    store: StoreResponseMini = Depends(get_staff_store),
    staff: Staff = Depends(get_staff),
    db: AsyncSession = Depends(get_db),
):
    is_owner = staff.staff_id == "OWNER" or getattr(staff, "role", None) == "owner"
    user_id = getattr(staff, "user_id", None)
    if is_owner and not user_id:
        user_id = await db.scalar(
            select(Store.user_id).where(Store.store_id == store.store_id)
        )

    target_conditions = [
        Notification.scope == NotificationScope.GLOBAL,
        (Notification.scope == NotificationScope.STORE) & (Notification.target_id == store.store_id),
    ]
    if user_id:
        target_conditions.append(
            (Notification.scope == NotificationScope.PERSONAL) & (Notification.target_id == user_id)
        )

    stmt = (
        select(Notification)
        .where(or_(*target_conditions))
        .order_by(Notification.created_at.desc())
        .limit(limit)
    )
    notifications = (await db.scalars(stmt)).all()

    read_ids = set()
    if notifications and user_id:
        notif_uuids = [n.notification_id for n in notifications]
        read_stmt = select(NotificationRead.notification_id).where(
            NotificationRead.user_id == user_id,
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
    staff: Staff = Depends(get_staff),
    db: AsyncSession = Depends(get_db),
):
    is_owner = staff.staff_id == "OWNER" or getattr(staff, "role", None) == "owner"
    user_id = getattr(staff, "user_id", None)
    if is_owner and not user_id:
        user_id = await db.scalar(
            select(Store.user_id).where(Store.store_id == store.store_id)
        )

    if not user_id:
        return {"success": True}

    existing = await db.scalar(
        select(NotificationRead).where(
            NotificationRead.user_id == user_id,
            NotificationRead.notification_id == notification_id,
        )
    )
    if not existing:
        new_read = NotificationRead(
            user_id=user_id,
            notification_id=notification_id,
        )
        db.add(new_read)
        await db.flush()

    return {"success": True}


@router.get("/vapid-public-key")
async def get_vapid_public_key():
    return {"public_key": notification_manager.get_public_key()}


@router.post("/subscribe", status_code=status.HTTP_201_CREATED)
async def subscribe_staff(
    store_id: uuid.UUID,
    body: PushSubscriptionBody,
    store: StoreResponseMini = Depends(get_staff_store),
    staff: Staff = Depends(get_staff),
    db: AsyncSession = Depends(get_db),
):
    sub_data = body.model_dump()
    is_owner = staff.staff_id == "OWNER" or getattr(staff, "role", None) == "owner"

    if is_owner:
        owner_user_id = getattr(staff, "user_id", None)
        if not owner_user_id:
            owner_user_id = await db.scalar(
                select(Store.user_id).where(Store.store_id == store.store_id)
            )
        if owner_user_id:
            existing = await db.execute(
                select(UserNotificationSubscription).where(
                    UserNotificationSubscription.user_id == owner_user_id
                )
            )
            for sub in existing.scalars().all():
                if sub.sub_info.get("endpoint") == body.endpoint:
                    return {"success": True, "message": "Already subscribed"}

            new_sub = UserNotificationSubscription(
                user_id=owner_user_id,
                sub_info=sub_data
            )
            db.add(new_sub)
            await db.flush()
            return {"success": True, "message": "Subscribed successfully"}
    else:
        existing = await db.execute(
            select(StaffNotificationSubscription).where(
                StaffNotificationSubscription.staff_id == staff.staff_id
            )
        )
        for sub in existing.scalars().all():
            if sub.sub_info.get("endpoint") == body.endpoint:
                return {"success": True, "message": "Already subscribed"}

        new_sub = StaffNotificationSubscription(
            staff_id=staff.staff_id,
            sub_info=sub_data
        )
        db.add(new_sub)
        await db.flush()
        return {"success": True, "message": "Subscribed successfully"}


@router.post("/unsubscribe")
async def unsubscribe_staff(
    store_id: uuid.UUID,
    body: PushSubscriptionBody,
    store: StoreResponseMini = Depends(get_staff_store),
    staff: Staff = Depends(get_staff),
    db: AsyncSession = Depends(get_db),
):
    is_owner = staff.staff_id == "OWNER" or getattr(staff, "role", None) == "owner"

    if is_owner:
        owner_user_id = getattr(staff, "user_id", None)
        if not owner_user_id:
            owner_user_id = await db.scalar(
                select(Store.user_id).where(Store.store_id == store.store_id)
            )
        if owner_user_id:
            existing = await db.execute(
                select(UserNotificationSubscription).where(
                    UserNotificationSubscription.user_id == owner_user_id
                )
            )
            for sub in existing.scalars().all():
                if sub.sub_info.get("endpoint") == body.endpoint:
                    await db.delete(sub)
            await db.flush()
    else:
        existing = await db.execute(
            select(StaffNotificationSubscription).where(
                StaffNotificationSubscription.staff_id == staff.staff_id
            )
        )
        for sub in existing.scalars().all():
            if sub.sub_info.get("endpoint") == body.endpoint:
                await db.delete(sub)
        await db.flush()

    return {"success": True, "message": "Unsubscribed successfully"}
