import asyncio
import json
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any
from sqlalchemy import select, delete, func
from pywebpush import webpush, WebPushException
from setting import settings
from models.config import LocalSession
from models.user import StaffNotificationSubscription, UserNotificationSubscription, Staff, User, StaffSession, UserSession
from models.business import Store
from models.stock import Sale


def _execute_webpush(sub_info: dict, payload: dict) -> bool:
    if not webpush:
        return False
    try:
        webpush(
            subscription_info=sub_info,
            data=json.dumps(payload),
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={"sub": settings.VAPID_CLAIM_EMAIL},
            timeout=5
        )
        return True
    except WebPushException as ex:
        response_code = getattr(ex.response, "status_code", None) if hasattr(ex, "response") else None
        if response_code in (404, 410):
            return False
        return False
    except Exception:
        return False


async def send_push_notification(ctx: dict, sub_info: dict, payload: dict) -> bool:
    return await asyncio.to_thread(_execute_webpush, sub_info, payload)


async def notify_staff_store(
    ctx: dict,
    store_id: str,
    title: str,
    body: str,
    data: dict | None = None
):
    payload = {"title": title, "body": body, "data": data or {}}
    async with LocalSession() as db:
        target_store_id = uuid.UUID(str(store_id))
        stmt = (
            select(StaffNotificationSubscription, Staff)
            .join(Staff, Staff.staff_id == StaffNotificationSubscription.staff_id)
            .where(Staff.store_id == target_store_id)
        )
        res = await db.execute(stmt)
        subs = res.all()

        dead_subs = []
        for sub_rec, _ in subs:
            success = await asyncio.to_thread(_execute_webpush, sub_rec.sub_info, payload)
            if not success:
                dead_subs.append(sub_rec.id)

        if dead_subs:
            await db.execute(
                delete(StaffNotificationSubscription).where(
                    StaffNotificationSubscription.id.in_(dead_subs)
                )
            )
            await db.commit()


async def notify_owner(
    ctx: dict,
    user_id: str,
    title: str,
    body: str,
    data: dict | None = None
):
    payload = {"title": title, "body": body, "data": data or {}}
    async with LocalSession() as db:
        target_user_id = uuid.UUID(str(user_id))
        stmt = select(UserNotificationSubscription).where(
            UserNotificationSubscription.user_id == target_user_id
        )
        res = await db.execute(stmt)
        subs = res.scalars().all()

        dead_subs = []
        for sub_rec in subs:
            success = await asyncio.to_thread(_execute_webpush, sub_rec.sub_info, payload)
            if not success:
                dead_subs.append(sub_rec.id)

        if dead_subs:
            await db.execute(
                delete(UserNotificationSubscription).where(
                    UserNotificationSubscription.id.in_(dead_subs)
                )
            )
            await db.commit()


async def notify_store(
    ctx: dict,
    store_id: str,
    title: str,
    body: str,
    data: dict | None = None
):
    await notify_staff_store(ctx, store_id, title, body, data)
    async with LocalSession() as db:
        target_store_id = uuid.UUID(str(store_id))
        store_res = await db.execute(select(Store).where(Store.store_id == target_store_id))
        store = store_res.scalar_one_or_none()
        if store and store.user_id:
            await notify_owner(ctx, str(store.user_id), title, body, data)


async def notify_low_stock(
    ctx: dict,
    store_id: str,
    product_name: str,
    current_stock: int,
    min_stock: int
):
    title = "Low Stock Alert"
    body = f"{product_name} is running low ({current_stock} remaining, minimum: {min_stock})."
    data = {"type": "low_stock", "store_id": str(store_id), "product_name": product_name}
    await notify_store(ctx, store_id, title, body, data)


async def notify_credit_sale(
    ctx: dict,
    store_id: str,
    customer_name: str,
    debt_amount: float,
    total_debt: float
):
    title = "Credit Sale Recorded"
    body = f"New debt of ₦{debt_amount:,.2f} recorded for {customer_name}. Total balance: ₦{total_debt:,.2f}."
    data = {"type": "credit_sale", "store_id": str(store_id), "customer_name": customer_name}
    await notify_store(ctx, store_id, title, body, data)


async def notify_staff_login(
    ctx: dict,
    store_id: str,
    staff_name: str,
    device_info: str = "Register Terminal"
):
    title = "Staff Terminal Login"
    body = f"{staff_name} signed into {device_info}."
    data = {"type": "staff_login", "store_id": str(store_id), "staff_name": staff_name}
    await notify_store(ctx, store_id, title, body, data)


async def cron_daily_sales_digest(ctx: dict):
    now = datetime.now(timezone.utc)
    today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)

    async with LocalSession() as db:
        stores = (await db.execute(select(Store))).scalars().all()
        for s in stores:
            sales_res = await db.execute(
                select(func.count(Sale.id), func.sum(Sale.total_amount))
                .where(Sale.store_id == s.store_id, Sale.created_at >= today_start)
            )
            count, total = sales_res.first() or (0, 0)
            total_rev = total or 0.0

            if count > 0 and s.user_id:
                title = f"Daily Digest: {s.store_name}"
                body = f"Today's total: ₦{total_rev:,.2f} across {count} sales transactions."
                await notify_owner(ctx, str(s.user_id), title, body, {"type": "daily_digest", "store_id": str(s.store_id)})


async def cron_prune_expired_sessions(ctx: dict):
    now = datetime.now(timezone.utc)
    async with LocalSession() as db:
        await db.execute(delete(StaffSession).where(StaffSession.expired_at <= now))
        await db.execute(delete(UserSession).where(UserSession.expired_at <= now))
        await db.commit()
