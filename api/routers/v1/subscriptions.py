from datetime import datetime, timezone, timedelta
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from models.config import get_db
from models.user import User
from models.business import Store
from models.stock import Stock, Sale
from models.admin.plan import Plan
from models.subscription import UserSubscription
from schemas.subscription import (
    PlanStatus,
    SubscriptionStatus,
    PaymentChannel,
    PlanResponse,
    SubscriptionUsageResponse,
    CurrentSubscriptionResponse,
    SubscribeRequest,
    SubscribeResponse,
    CancelSubscriptionResponse,
    SubscriptionHistoryItem,
)
from schemas.business import StoreStatus
from libs.deps import get_current_user
from libs.payment import payment_manager, PaymentException
from libs.cache import get_cache, set_cache
from setting import settings
from worker.config import get_arq_pool
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions & Billing"])


@router.get("/plans", response_model=list[PlanResponse])
async def list_available_plans(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Check if user has EVER used any trial anywhere on any plan
    has_used_trial = (
        await db.scalar(
            select(func.count(UserSubscription.id)).where(
                UserSubscription.user_id == current_user.user_id,
                (UserSubscription.is_trial.is_(True)) | (UserSubscription.plan_id == "trial"),
            )
        )
        or 0
    ) > 0
    if not has_used_trial and getattr(current_user, "has_used_trial", False):
        has_used_trial = True

    # Standalone 'trial' plan is excluded
    cached_plans = await get_cache("kluda:cache:public_plans")
    if cached_plans is not None:
        plans = [PlanResponse(**p) for p in cached_plans]
    else:
        query = select(Plan).where(Plan.status == PlanStatus.AVAILABLE, Plan.slug != "trial")
        db_plans = (await db.scalars(query.order_by(Plan.price.asc()))).all()
        serialized = [PlanResponse.model_validate(p).model_dump(mode="json") for p in db_plans]
        await set_cache("kluda:cache:public_plans", serialized, expire_seconds=3600)
        plans = [PlanResponse(**p) for p in serialized]

    if has_used_trial:
        # Trial option and text must NOT be available if user has ever used any trial
        return [
            PlanResponse(
                id=p.id,
                slug=p.slug,
                name=p.name,
                description=p.description,
                price=p.price,
                interval=p.interval,
                has_trial=False,
                trial_duration_days=0,
                store_limit=p.store_limit,
                product_limit=p.product_limit,
                sales_limit_per_month=p.sales_limit_per_month,
                analytics_read_per_month=p.analytics_read_per_month,
                status=p.status,
                paystack_planid=p.paystack_planid,
            )
            for p in plans
        ]

    return plans


@router.get("/current", response_model=CurrentSubscriptionResponse)
async def get_current_subscription(
    store_id: uuid.UUID | None = Query(None, description="Optional store branch context"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_user_id = current_user.user_id
    is_owner = True
    owner_name = current_user.fullname

    if store_id:
        store = await db.scalar(select(Store).where(Store.store_id == store_id))
        if store:
            target_user_id = store.user_id
            is_owner = current_user.user_id == store.user_id

    owner = await db.scalar(
        select(User)
        .options(selectinload(User.current_subscription))
        .where(User.user_id == target_user_id)
    )

    if owner and owner.fullname:
        owner_name = owner.fullname

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
        plan = await db.scalar(
            select(Plan).where(Plan.slug == "free")
        )
    if not plan:
        plan = await db.scalar(
            select(Plan).where(Plan.status == PlanStatus.AVAILABLE).order_by(Plan.price.asc())
        )

    if not plan:
        plan = Plan(
            id=1,
            slug="starter",
            name="Starter Plan",
            description="Standard single-terminal retail operations.",
            price=0,
            store_limit=1,
            product_limit=100,
            sales_limit_per_month=500,
            analytics_read_per_month=100,
            status=PlanStatus.AVAILABLE,
        )

    now = datetime.now(timezone.utc)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    stores_count = (
        await db.scalar(
            select(func.count(Store.id)).where(
                Store.user_id == target_user_id, Store.status == StoreStatus.ACTIVE
            )
        )
    ) or 0

    products_count = (
        await db.scalar(
            select(func.count(Stock.id))
            .join(Store, Stock.store_id == Store.store_id)
            .where(Store.user_id == target_user_id)
        )
    ) or 0

    monthly_sales_count = (
        await db.scalar(
            select(func.count(Sale.id))
            .join(Store, Sale.store_id == Store.store_id)
            .where(
                Store.user_id == target_user_id,
                Sale.status != "cancelled",
                Sale.created_at >= start_of_month,
            )
        )
    ) or 0

    usage = SubscriptionUsageResponse(
        stores_count=stores_count,
        stores_limit=plan.store_limit or 1,
        products_count=products_count,
        products_limit=plan.product_limit or 100,
        monthly_sales_count=monthly_sales_count,
        monthly_sales_limit=plan.sales_limit_per_month or 500,
        monthly_analytics_count=12,
        monthly_analytics_limit=plan.analytics_read_per_month or 100,
    )

    sub_status = current_sub.status if current_sub else SubscriptionStatus.ACTIVE
    sub_amount = current_sub.amount if current_sub else plan.price
    next_renewal = (
        current_sub.next_renewal if current_sub else (now + timedelta(days=30))
    )

    has_used_trial = (
        await db.scalar(
            select(func.count(UserSubscription.id)).where(
                UserSubscription.user_id == target_user_id,
                (UserSubscription.is_trial.is_(True)) | (UserSubscription.plan_id == "trial"),
            )
        )
        or 0
    ) > 0
    if not has_used_trial and getattr(current_user, "has_used_trial", False):
        has_used_trial = True

    from libs.quota_token import generate_signed_quota_token
    token_info = await generate_signed_quota_token(
        db=db,
        owner_user_id=target_user_id,
        store_id=store_id,
    )

    return CurrentSubscriptionResponse(
        subscription_id=current_sub.subscription_id if current_sub else None,
        plan=PlanResponse.model_validate(plan),
        status=sub_status,
        amount=sub_amount,
        next_renewal=next_renewal,
        usage=usage,
        is_owner=is_owner,
        owner_name=owner_name,
        has_used_trial=has_used_trial,
        is_trial=bool(getattr(current_sub, "is_trial", False)),
        quota_token=token_info["token"],
        max_offline_days=token_info["payload"]["max_offline_days"],
        offline_lease_expires_at=token_info["payload"]["offline_lease_expires_at"],
        offline_disclaimer=token_info["payload"]["disclaimer"],
    )


@router.post("/subscribe", response_model=SubscribeResponse)
async def subscribe_plan(
    payload: SubscribeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_slug = payload.plan_slug.strip().lower()

    if target_slug == "trial":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Standalone trial plan is not available",
        )

    plan = await db.scalar(
        select(Plan).where(
            Plan.slug == target_slug,
            Plan.status == PlanStatus.AVAILABLE,
            Plan.slug != "trial",
        )
    )
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requested subscription plan is not available",
        )

    # Free trial opt-in validation
    if payload.is_trial:
        if not plan.has_trial or not plan.trial_duration_days or plan.trial_duration_days <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This plan does not offer a free trial",
            )

        # Enforce on API: check if user has EVER used ANY trial anywhere before
        has_used_trial = (
            await db.scalar(
                select(func.count(UserSubscription.id)).where(
                    UserSubscription.user_id == current_user.user_id,
                    (UserSubscription.is_trial.is_(True)) | (UserSubscription.plan_id == "trial"),
                )
            )
            or 0
        ) > 0
        if not has_used_trial and getattr(current_user, "has_used_trial", False):
            has_used_trial = True

        if has_used_trial:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already used your one-time trial on an account before",
            )

        # Activate trial immediately - NO Paystack gateway called!
        duration = plan.trial_duration_days
        new_sub = UserSubscription(
            user_id=current_user.user_id,
            plan_id=plan.slug,
            status=SubscriptionStatus.ACTIVE,
            amount=0,
            is_trial=True,
            payment_channel=PaymentChannel.PAYSTACK,
            next_renewal=datetime.now(timezone.utc) + timedelta(days=duration),
            idempotency_key=f"trial_{plan.slug}_{current_user.user_id}_{uuid.uuid4().hex[:6]}",
            description=f"{duration}-Day Free Trial of {plan.name}",
        )
        db.add(new_sub)
        current_user.has_used_trial = True
        await db.flush()
        current_user.current_subscription_id = new_sub.subscription_id
        await db.commit()

        return SubscribeResponse(
            status="active",
            redirect_url=None,
            reference=None,
            message=f"{duration}-Day Free Trial of {plan.name} activated successfully!",
        )

    # Free plan: activate immediately without gateway checkout
    if plan.price == 0 or target_slug == "free":
        new_sub = UserSubscription(
            user_id=current_user.user_id,
            plan_id="free",
            status=SubscriptionStatus.ACTIVE,
            amount=0,
            payment_channel=PaymentChannel.PAYSTACK,
            next_renewal=datetime.now(timezone.utc) + timedelta(days=36500),
            idempotency_key=f"free_{current_user.user_id}_{uuid.uuid4().hex[:8]}",
        )
        db.add(new_sub)
        await db.flush()
        current_user.current_subscription_id = new_sub.subscription_id
        await db.commit()

        return SubscribeResponse(
            status="active",
            redirect_url=None,
            reference=None,
            message=f"Subscribed to {plan.name}",
        )

    auth_data = current_user.paystack_authorization
    auth_code = (
        auth_data.get("authorization_code") if isinstance(auth_data, dict) else None
    )

    # Change of plan with stored authorization: charge card immediately
    if auth_code:
        ref = f"sub_charge_{uuid.uuid4().hex[:12]}"
        try:
            # Paystack amounts are in subunit (kobo for NGN)
            charge_res = await payment_manager.paystack_charge_authorization(
                authorization_code=auth_code,
                email=current_user.email,
                amount=plan.price,
                reference=ref,
                metadata={
                    "user_id": str(current_user.user_id),
                    "plan_slug": plan.slug,
                },
            )

            charge_data = charge_res.get("data", {})
            if charge_data.get("status") == "success":
                new_sub = UserSubscription(
                    user_id=current_user.user_id,
                    plan_id=plan.slug,
                    status=SubscriptionStatus.ACTIVE,
                    amount=plan.price,
                    reference=ref,
                    idempotency_key=f"charge_{ref}",
                    payment_channel=PaymentChannel.PAYSTACK,
                    next_renewal=datetime.now(timezone.utc) + timedelta(days=30),
                )
                db.add(new_sub)
                await db.flush()
                current_user.current_subscription_id = new_sub.subscription_id
                await db.commit()

                pool = await get_arq_pool()
                await pool.enqueue_job(
                    "send_subscription_notification_email",
                    recipient_email=current_user.email,
                    recipient_name=current_user.fullname,
                    event_type="payment_success",
                    amount=plan.price,
                    plan_name=plan.name,
                    reference=ref,
                    next_renewal=new_sub.next_renewal.strftime("%B %d, %Y"),
                )
                await pool.enqueue_job(
                    "notify_user_personal",
                    str(current_user.user_id),
                    "Plan Updated",
                    f"Your subscription was changed to {plan.name}.",
                    {"type": "subscription_success", "url": "/marchant/billing"},
                )

                return SubscribeResponse(
                    status="active",
                    redirect_url=None,
                    reference=ref,
                    message=f"Successfully switched to {plan.name}",
                )
        except PaymentException as pe:
            logger.warning(
                "Charge authorization failed, redirecting to checkout",
                error=pe.message,
            )

    # First subscription or failed direct charge: initialize transaction with redirect URL
    ref = f"sub_init_{uuid.uuid4().hex[:12]}"
    domain = settings.DOMAIN_NAME
    callback_url = (
        f"https://app.{domain}/marchant/billing"
        if "localhost" not in domain
        else "http://localhost:3000/marchant/billing"
    )

    try:
        # Paystack amounts are in subunit (kobo for NGN)
        init_res = await payment_manager.paystack_initialize_transaction(
            email=current_user.email,
            amount=plan.price,
            plan=plan.paystack_planid,
            reference=ref,
            callback_url=callback_url,
            metadata={
                "user_id": str(current_user.user_id),
                "plan_slug": plan.slug,
            },
        )
        auth_url = init_res.get("data", {}).get("authorization_url")
        return SubscribeResponse(
            status="pending_payment",
            redirect_url=auth_url,
            reference=ref,
            message="Redirecting to payment checkout",
        )
    except PaymentException as pe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to initialize payment: {pe.message}",
        )


@router.post("/cancel", response_model=CancelSubscriptionResponse)
async def cancel_subscription(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.current_subscription_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active subscription found to cancel",
        )

    current_sub = await db.scalar(
        select(UserSubscription).where(
            UserSubscription.subscription_id == current_user.current_subscription_id
        )
    )

    if not current_sub or current_sub.status == SubscriptionStatus.EXPIRED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subscription is already cancelled or expired",
        )

    # Disable recurring subscription on Paystack if linked
    if current_sub.paystack_subscription_code:
        try:
            await payment_manager.paystack_disable_subscription(
                subscription_code=current_sub.paystack_subscription_code,
                email_token="",
            )
        except Exception as ex:
            logger.warning("Failed to disable Paystack subscription directly", error=str(ex))

    current_sub.status = SubscriptionStatus.EXPIRED
    await db.flush()

    # User falls back to free plan
    now = datetime.now(timezone.utc)
    free_sub = UserSubscription(
        user_id=current_user.user_id,
        plan_id="free",
        status=SubscriptionStatus.ACTIVE,
        amount=0,
        payment_channel=PaymentChannel.PAYSTACK,
        next_renewal=now + timedelta(days=36500),
        idempotency_key=f"fallback_free_{current_user.user_id}_{uuid.uuid4().hex[:8]}",
    )
    db.add(free_sub)
    await db.flush()
    current_user.current_subscription_id = free_sub.subscription_id
    await db.commit()

    pool = await get_arq_pool()
    await pool.enqueue_job(
        "notify_user_personal",
        str(current_user.user_id),
        "Subscription Cancelled",
        "Your subscription has been cancelled. Your account is now on the Free Tier.",
        {"type": "subscription_disabled", "url": "/marchant/billing"},
    )

    return CancelSubscriptionResponse(
        status="cancelled",
        message="Subscription cancelled. Account reverted to Free Tier.",
    )


@router.get("/history", response_model=list[SubscriptionHistoryItem])
async def list_subscription_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve billing, payment, and subscription history for the current merchant."""
    query = (
        select(UserSubscription)
        .options(selectinload(UserSubscription.plan))
        .where(UserSubscription.user_id == current_user.user_id)
        .order_by(UserSubscription.created_at.desc())
    )
    result = await db.scalars(query)
    subscriptions = result.all()

    items = []
    for sub in subscriptions:
        plan_name = sub.plan.name if sub.plan else sub.plan_id.capitalize()
        items.append(
            SubscriptionHistoryItem(
                id=sub.id,
                subscription_id=sub.subscription_id,
                plan_slug=sub.plan_id,
                plan_name=plan_name,
                status=sub.status,
                amount=sub.amount,
                is_trial=sub.is_trial,
                reference=sub.reference,
                payment_channel=sub.payment_channel,
                created_at=sub.created_at,
                next_renewal=sub.next_renewal,
                description=sub.description,
            )
        )
    return items

