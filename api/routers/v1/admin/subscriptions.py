import uuid
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from models.config import get_db
from models.user import User
from models.admin.user import Admin
from models.admin.plan import Plan
from models.subscription import UserSubscription
from schemas.subscription import PlanStatus, SubscriptionStatus, PaymentChannel
from libs.deps import require_superadmin, get_admin
from libs.audit import record_audit_log
from worker.config import get_arq_pool
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/subscriptions", tags=["Admin Subscription Management"])


class GrantSubscriptionRequest(BaseModel):
    user_id: uuid.UUID
    plan_slug: str
    duration_days: int = Field(default=14, gt=0, le=3650, description="Duration of offer in days")
    description: str = Field(min_length=3, max_length=500, description="Audit reason, e.g. Referral reward or VIP offer")
    amount: int = Field(default=0, ge=0, description="Amount in subunit (kobo for NGN)")


class GrantSubscriptionResponse(BaseModel):
    status: str
    subscription_id: uuid.UUID
    user_id: uuid.UUID
    user_email: str
    plan_slug: str
    plan_name: str
    amount: int
    duration_days: int
    next_renewal: datetime
    description: str
    message: str


class GrantedSubscriptionItem(BaseModel):
    subscription_id: uuid.UUID
    user_id: uuid.UUID
    user_email: str
    user_name: str | None
    plan_slug: str
    plan_name: str
    amount: int
    status: str
    description: str | None
    created_at: datetime
    next_renewal: datetime


@router.post("/grant", response_model=GrantSubscriptionResponse)
async def grant_subscription_offer(
    payload: GrantSubscriptionRequest,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_superadmin()),
):
    target_user = await db.scalar(
        select(User)
        .options(selectinload(User.current_subscription))
        .where(User.user_id == payload.user_id)
    )
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant user not found",
        )

    clean_slug = payload.plan_slug.strip().lower()
    target_plan = await db.scalar(
        select(Plan).where(
            Plan.slug == clean_slug,
            Plan.status == PlanStatus.AVAILABLE,
        )
    )
    if not target_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription plan '{payload.plan_slug}' is not available",
        )

    # Retire previous active subscription if exists
    if target_user.current_subscription:
        target_user.current_subscription.status = SubscriptionStatus.EXPIRED
        await db.flush()

    now = datetime.now(timezone.utc)
    renewal_date = now + timedelta(days=payload.duration_days)

    new_sub = UserSubscription(
        user_id=target_user.user_id,
        plan_id=target_plan.slug,
        status=SubscriptionStatus.ACTIVE,
        amount=payload.amount,
        payment_channel=PaymentChannel.PAYSTACK,
        description=payload.description.strip(),
        next_renewal=renewal_date,
        idempotency_key=f"grant_{uuid.uuid4().hex[:12]}",
    )
    db.add(new_sub)
    await db.flush()

    target_user.current_subscription_id = new_sub.subscription_id
    await db.commit()
    await db.refresh(new_sub)

    # Record administrative audit trail
    await record_audit_log(
        db=db,
        admin_id=admin.admin_id,
        action="GRANT_SUBSCRIPTION_OFFER",
        target_type="user_subscription",
        target_id=new_sub.subscription_id,
        details={
            "recipient_user_id": str(target_user.user_id),
            "recipient_email": target_user.email,
            "plan_slug": target_plan.slug,
            "plan_name": target_plan.name,
            "duration_days": payload.duration_days,
            "amount": payload.amount,
            "reason": payload.description.strip(),
        },
    )

    try:
        pool = await get_arq_pool()
        await pool.enqueue_job(
            "notify_user_personal",
            str(target_user.user_id),
            f"Special Plan Activated: {target_plan.name}",
            f"You have been granted {payload.duration_days} days of {target_plan.name}. Reason: {payload.description.strip()}",
            {"type": "subscription_grant", "url": "/marchant/billing"},
        )
    except Exception as ex:
        logger.warning("Failed to enqueue user notification for subscription grant", error=str(ex))

    return GrantSubscriptionResponse(
        status="active",
        subscription_id=new_sub.subscription_id,
        user_id=target_user.user_id,
        user_email=target_user.email,
        plan_slug=target_plan.slug,
        plan_name=target_plan.name,
        amount=payload.amount,
        duration_days=payload.duration_days,
        next_renewal=renewal_date,
        description=new_sub.description or "",
        message=f"Successfully granted {target_plan.name} to {target_user.email} for {payload.duration_days} days.",
    )


@router.get("/grants", response_model=list[GrantedSubscriptionItem])
async def list_granted_subscriptions(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_admin),
):
    stmt = (
        select(UserSubscription)
        .options(selectinload(UserSubscription.user), selectinload(UserSubscription.plan))
        .where(UserSubscription.description.is_not(None))
        .order_by(desc(UserSubscription.created_at))
        .limit(limit)
    )
    results = await db.scalars(stmt)

    items = []
    for sub in results.all():
        items.append(
            GrantedSubscriptionItem(
                subscription_id=sub.subscription_id,
                user_id=sub.user_id,
                user_email=sub.user.email if sub.user else "Unknown",
                user_name=sub.user.fullname if sub.user else None,
                plan_slug=sub.plan_id,
                plan_name=sub.plan.name if sub.plan else sub.plan_id,
                amount=sub.amount,
                status=sub.status.value if hasattr(sub.status, "value") else str(sub.status),
                description=sub.description,
                created_at=sub.created_at,
                next_renewal=sub.next_renewal,
            )
        )
    return items
