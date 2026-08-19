import uuid
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from models.config import get_db
from models.user import Staff, StaffNotificationSubscription
from libs.deps import get_staff, get_staff_store
from schemas.business import StoreResponseMini
from libs.notification_manager import notification_manager

router = APIRouter(prefix="/{store_id}/notifications", tags=["Staff Notifications"])


class PushSubscriptionBody(BaseModel):
    endpoint: str
    keys: dict
    expirationTime: float | None = None


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
    await db.commit()
    return {"success": True, "message": "Subscribed successfully"}


@router.post("/unsubscribe")
async def unsubscribe_staff(
    store_id: uuid.UUID,
    body: PushSubscriptionBody,
    store: StoreResponseMini = Depends(get_staff_store),
    staff: Staff = Depends(get_staff),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(StaffNotificationSubscription).where(
            StaffNotificationSubscription.staff_id == staff.staff_id
        )
    )
    for sub in existing.scalars().all():
        if sub.sub_info.get("endpoint") == body.endpoint:
            await db.delete(sub)
    await db.commit()
    return {"success": True, "message": "Unsubscribed successfully"}
