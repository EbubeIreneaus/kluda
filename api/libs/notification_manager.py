import asyncio
import json
import uuid
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from setting import settings
from models.user import StaffNotificationSubscription, UserNotificationSubscription, Staff
from models.business import Store
from models.config import LocalSession
from pywebpush import webpush, WebPushException
from worker.config import get_arq_pool


class NotificationManager:
    def __init__(self):
        self.public_key = settings.VAPID_PUBLIC_KEY
        self.private_key = settings.VAPID_PRIVATE_KEY
        self.claims = {"sub": settings.VAPID_CLAIM_EMAIL}

    def get_public_key(self) -> str:
        return self.public_key

    def _send_push_sync(self, sub_info: dict, payload: dict) -> bool:
        if not webpush:
            return False
        try:
            webpush(
                subscription_info=sub_info,
                data=json.dumps(payload),
                vapid_private_key=self.private_key,
                vapid_claims=self.claims,
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

    async def _send_push(self, sub_info: dict, payload: dict) -> bool:
        return await asyncio.to_thread(self._send_push_sync, sub_info, payload)

    async def enqueue_low_stock(
        self,
        store_id: uuid.UUID | str,
        product_name: str,
        current_stock: int,
        min_stock: int
    ):
        try:
            pool = await get_arq_pool()
            await pool.enqueue_job("notify_low_stock", str(store_id), product_name, current_stock, min_stock)
        except Exception:
            title = "Low Stock Alert"
            body = f"{product_name} is running low ({current_stock} remaining, minimum: {min_stock})."
            await self.send_to_store(store_id, title, body, {"type": "low_stock", "store_id": str(store_id)})

    async def enqueue_credit_sale(
        self,
        store_id: uuid.UUID | str,
        customer_name: str,
        debt_amount: float,
        total_debt: float
    ):
        try:
            pool = await get_arq_pool()
            await pool.enqueue_job("notify_credit_sale", str(store_id), customer_name, debt_amount, total_debt)
        except Exception:
            title = "Credit Sale Recorded"
            body = f"New debt of ₦{debt_amount:,.2f} recorded for {customer_name}. Total balance: ₦{total_debt:,.2f}."
            await self.send_to_store(store_id, title, body, {"type": "credit_sale", "store_id": str(store_id)})

    async def enqueue_staff_login(
        self,
        store_id: uuid.UUID | str,
        staff_name: str,
        device_info: str = "Register Terminal"
    ):
        try:
            pool = await get_arq_pool()
            await pool.enqueue_job("notify_staff_login", str(store_id), staff_name, device_info)
        except Exception:
            title = "Staff Terminal Login"
            body = f"{staff_name} signed into {device_info}."
            await self.send_to_store(store_id, title, body, {"type": "staff_login", "store_id": str(store_id)})

    async def send_to_staff(
        self,
        store_id: uuid.UUID | str,
        title: str,
        body: str,
        data: dict | None = None,
        db: AsyncSession | None = None
    ):
        payload = {"title": title, "body": body, "data": data or {}}
        should_close = False
        if db is None:
            session = LocalSession()
            db = session
            should_close = True

        try:
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
                success = await self._send_push(sub_rec.sub_info, payload)
                if not success:
                    dead_subs.append(sub_rec.id)

            if dead_subs:
                await db.execute(
                    delete(StaffNotificationSubscription).where(
                        StaffNotificationSubscription.id.in_(dead_subs)
                    )
                )
                await db.commit()
        finally:
            if should_close:
                await db.close()

    async def send_to_owner(
        self,
        user_id: uuid.UUID | str,
        title: str,
        body: str,
        data: dict | None = None,
        db: AsyncSession | None = None
    ):
        payload = {"title": title, "body": body, "data": data or {}}
        should_close = False
        if db is None:
            session = LocalSession()
            db = session
            should_close = True

        try:
            target_user_id = uuid.UUID(str(user_id))
            stmt = select(UserNotificationSubscription).where(
                UserNotificationSubscription.user_id == target_user_id
            )
            res = await db.execute(stmt)
            subs = res.scalars().all()

            dead_subs = []
            for sub_rec in subs:
                success = await self._send_push(sub_rec.sub_info, payload)
                if not success:
                    dead_subs.append(sub_rec.id)

            if dead_subs:
                await db.execute(
                    delete(UserNotificationSubscription).where(
                        UserNotificationSubscription.id.in_(dead_subs)
                    )
                )
                await db.commit()
        finally:
            if should_close:
                await db.close()

    async def send_to_store(
        self,
        store_id: uuid.UUID | str,
        title: str,
        body: str,
        data: dict | None = None,
        db: AsyncSession | None = None
    ):
        should_close = False
        if db is None:
            session = LocalSession()
            db = session
            should_close = True

        try:
            target_store_id = uuid.UUID(str(store_id))
            store_res = await db.execute(select(Store).where(Store.store_id == target_store_id))
            store = store_res.scalar_one_or_none()

            await self.send_to_staff(store_id, title, body, data, db=db)
            if store and store.user_id:
                await self.send_to_owner(store.user_id, title, body, data, db=db)
        finally:
            if should_close:
                await db.close()

    async def broadcast_all(
        self,
        title: str,
        body: str,
        data: dict | None = None,
        db: AsyncSession | None = None
    ):
        payload = {"title": title, "body": body, "data": data or {}}
        should_close = False
        if db is None:
            session = LocalSession()
            db = session
            should_close = True

        try:
            staff_subs = (await db.execute(select(StaffNotificationSubscription))).scalars().all()
            owner_subs = (await db.execute(select(UserNotificationSubscription))).scalars().all()

            dead_staff = []
            for sub in staff_subs:
                if not await self._send_push(sub.sub_info, payload):
                    dead_staff.append(sub.id)

            dead_owner = []
            for sub in owner_subs:
                if not await self._send_push(sub.sub_info, payload):
                    dead_owner.append(sub.id)

            if dead_staff:
                await db.execute(
                    delete(StaffNotificationSubscription).where(
                        StaffNotificationSubscription.id.in_(dead_staff)
                    )
                )
            if dead_owner:
                await db.execute(
                    delete(UserNotificationSubscription).where(
                        UserNotificationSubscription.id.in_(dead_owner)
                    )
                )
            if dead_staff or dead_owner:
                await db.commit()
        finally:
            if should_close:
                await db.close()


notification_manager = NotificationManager()
