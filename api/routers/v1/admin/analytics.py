from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from models.config import get_db
from models.business import Store
from models.user import User
from models.subscription import UserSubscription
from schemas.subscription import SubscriptionStatus
from models.admin.ticket import SupportTicket, TicketStatus
from models.admin.email import EmailThread, EmailThreadStatus
from models.admin.metric import DailyPlatformMetric
from models.admin.user import Admin
from schemas.admin.metric import DailyPlatformMetricResponse
from schemas.admin.user import AdminPermission
from schemas.business import StoreStatus
from libs.deps import require_admin_permission


router = APIRouter(prefix="/analytics", tags=["Admin Analytics"])


@router.get("/overview")
async def get_analytics_overview(
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_admin_permission(AdminPermission.VIEW_ANALYTICS)),
):
    now = datetime.now(timezone.utc)
    today = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)

    total_merchants = await db.scalar(select(func.count(User.id))) or 0
    new_merchants_today = await db.scalar(select(func.count(User.id)).where(User.created_at >= today)) or 0
    total_stores = await db.scalar(select(func.count(Store.id))) or 0
    active_stores = await db.scalar(select(func.count(Store.id)).where(Store.status == StoreStatus.ACTIVE)) or 0

    # SaaS Subscription metrics
    active_paid_subs = (
        await db.scalar(
            select(func.count(UserSubscription.id))
            .where(
                UserSubscription.status == SubscriptionStatus.ACTIVE,
                UserSubscription.plan_id.in_(["growth", "enterprise"]),
            )
        )
    ) or 0

    trial_subs = (
        await db.scalar(
            select(func.count(UserSubscription.id))
            .where(
                UserSubscription.status == SubscriptionStatus.ACTIVE,
                UserSubscription.plan_id == "trial",
            )
        )
    ) or 0

    free_subs = (
        await db.scalar(
            select(func.count(UserSubscription.id))
            .where(
                UserSubscription.status == SubscriptionStatus.ACTIVE,
                UserSubscription.plan_id == "free",
            )
        )
    ) or 0

    # Monthly Recurring Revenue (sum of active paid subscriptions, amount in kobo -> converted to Naira)
    mrr_kobo = (
        await db.scalar(
            select(func.coalesce(func.sum(UserSubscription.amount), 0))
            .where(
                UserSubscription.status == SubscriptionStatus.ACTIVE,
                UserSubscription.amount > 0,
            )
        )
    ) or 0
    mrr_naira = int(mrr_kobo / 100)

    # Subscription distribution breakdown
    dist_rows = await db.execute(
        select(UserSubscription.plan_id, func.count(UserSubscription.id))
        .where(UserSubscription.status == SubscriptionStatus.ACTIVE)
        .group_by(UserSubscription.plan_id)
    )
    dist_map = {row[0]: row[1] for row in dist_rows.all()}

    open_tickets = await db.scalar(select(func.count(SupportTicket.id)).where(SupportTicket.status == TicketStatus.OPEN)) or 0
    unread_threads = await db.scalar(select(func.count(EmailThread.id)).where(EmailThread.status == EmailThreadStatus.UNREAD)) or 0

    return {
        "total_merchants": total_merchants,
        "new_merchants_today": new_merchants_today,
        "total_stores": total_stores,
        "active_stores": active_stores,
        "active_paid_subscriptions": active_paid_subs,
        "trial_subscriptions": trial_subs,
        "free_subscriptions": free_subs,
        "monthly_recurring_revenue": mrr_naira,
        "subscription_distribution": [
            {"plan": "Free Tier", "slug": "free", "count": dist_map.get("free", free_subs)},
            {"plan": "30-Day Pro Trial", "slug": "trial", "count": dist_map.get("trial", trial_subs)},
            {"plan": "Merchant Growth", "slug": "growth", "count": dist_map.get("growth", 0)},
            {"plan": "Enterprise Multi-Store", "slug": "enterprise", "count": dist_map.get("enterprise", 0)},
        ],
        "open_tickets": open_tickets,
        "unread_threads": unread_threads,
    }


@router.get("/chart", response_model=list[DailyPlatformMetricResponse])
async def get_chart_data(
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_admin_permission(AdminPermission.VIEW_ANALYTICS)),
):
    stmt = select(DailyPlatformMetric).order_by(DailyPlatformMetric.date.desc()).limit(30)
    result = await db.scalars(stmt)
    return list(reversed(result.all()))
