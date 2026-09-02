import hmac
import hashlib
import json
import base64
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from models.user import User
from models.business import Store
from models.stock import Stock, Sale
from models.admin.plan import Plan
from models.subscription import UserSubscription
from models.admin.setting import SystemSetting
from schemas.subscription import PlanStatus, SubscriptionStatus
from schemas.business import StoreStatus
from setting import settings


async def get_max_offline_days(db: AsyncSession) -> int:
    setting = await db.scalar(
        select(SystemSetting).where(SystemSetting.key == "pos_offline_policy")
    )
    if setting and isinstance(setting.value, dict):
        return int(setting.value.get("max_offline_days", 3))
    return 3


async def generate_signed_quota_token(
    db: AsyncSession,
    owner_user_id: uuid.UUID,
    store_id: uuid.UUID | None = None,
) -> dict:
    owner = await db.scalar(
        select(User).where(User.user_id == owner_user_id)
    )

    current_sub = None
    if owner and owner.current_subscription_id:
        current_sub = await db.scalar(
            select(UserSubscription).where(
                UserSubscription.subscription_id == owner.current_subscription_id
            )
        )

    plan = None
    if current_sub and current_sub.plan_id:
        plan = await db.scalar(select(Plan).where(Plan.slug == current_sub.plan_id))

    if not plan:
        plan = await db.scalar(select(Plan).where(Plan.slug == "free"))
    if not plan:
        plan = await db.scalar(
            select(Plan).where(Plan.status == PlanStatus.AVAILABLE).order_by(Plan.price.asc())
        )

    now = datetime.now(timezone.utc)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    stores_count = (
        await db.scalar(
            select(func.count(Store.id)).where(
                Store.user_id == owner_user_id, Store.status == StoreStatus.ACTIVE
            )
        )
    ) or 0

    products_count = (
        await db.scalar(
            select(func.count(Stock.id))
            .join(Store, Stock.store_id == Store.store_id)
            .where(Store.user_id == owner_user_id, Stock.deleted == False)
        )
    ) or 0

    monthly_sales_count = (
        await db.scalar(
            select(func.count(Sale.id))
            .join(Store, Sale.store_id == Store.store_id)
            .where(
                Store.user_id == owner_user_id,
                Sale.status != "cancelled",
                Sale.created_at >= start_of_month,
            )
        )
    ) or 0

    max_offline_days = await get_max_offline_days(db)
    offline_lease_expires_at = int((now + timedelta(days=max_offline_days)).timestamp())

    sub_status = current_sub.status.value if current_sub and hasattr(current_sub.status, "value") else (str(current_sub.status) if current_sub else "active")
    analytics_used = current_sub.analytics_used if current_sub else 0

    payload = {
        "owner_user_id": str(owner_user_id),
        "store_id": str(store_id) if store_id else None,
        "subscription_id": str(current_sub.subscription_id) if current_sub else None,
        "plan_slug": plan.slug if plan else "free",
        "plan_name": plan.name if plan else "Free Tier",
        "status": sub_status.upper(),
        "monthly_sales_count": monthly_sales_count,
        "monthly_sales_limit": plan.sales_limit_per_month if plan else 200,
        "products_count": products_count,
        "products_limit": plan.product_limit if plan else 100,
        "stores_count": stores_count,
        "stores_limit": plan.store_limit if plan else 1,
        "analytics_used": analytics_used,
        "analytics_limit": plan.analytics_read_per_month if plan else 50,
        "max_offline_days": max_offline_days,
        "issued_at": int(now.timestamp()),
        "offline_lease_expires_at": offline_lease_expires_at,
        "disclaimer": "Offline means service disruption won't affect sales. Not working offline without turning on data.",
    }

    raw_json = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    b64_payload = base64.urlsafe_b64encode(raw_json).decode("utf-8").rstrip("=")

    secret = getattr(settings, "SECRET_KEY", "kluda-offline-pos-key").encode("utf-8")
    signature = hmac.new(secret, b64_payload.encode("utf-8"), hashlib.sha256).hexdigest()

    token_str = f"{b64_payload}.{signature}"

    return {
        "payload": payload,
        "signature": signature,
        "token": token_str,
    }


def verify_signed_quota_token(token_str: str) -> tuple[bool, dict | None, str | None]:
    if not token_str or "." not in token_str:
        return False, None, "Invalid token structure"

    parts = token_str.split(".")
    if len(parts) != 2:
        return False, None, "Invalid token format"

    b64_payload, signature = parts
    secret = getattr(settings, "SECRET_KEY", "kluda-offline-pos-key").encode("utf-8")
    expected_sig = hmac.new(secret, b64_payload.encode("utf-8"), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected_sig, signature):
        return False, None, "Cryptographic signature mismatch: token has been tampered with"

    try:
        # Add padding back if necessary
        padded = b64_payload + "=" * (-len(b64_payload) % 4)
        raw_json = base64.urlsafe_b64decode(padded.encode("utf-8"))
        payload = json.loads(raw_json)
        return True, payload, None
    except Exception as e:
        return False, None, f"Failed to parse payload: {str(e)}"
