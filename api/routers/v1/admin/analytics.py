from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from models.config import get_db
from models.business import Store
from models.stock import Sale, Stock
from models.user import User, Staff
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
    total_staff = await db.scalar(select(func.count(Staff.id))) or 0
    total_products = await db.scalar(select(func.count(Stock.id))) or 0

    sales_stats = await db.execute(
        select(
            func.count(Sale.id).label("total_transactions"),
            func.coalesce(func.sum(Sale.amount_recived), 0).label("total_gmv"),
        )
    )
    sales_row = sales_stats.first()

    open_tickets = await db.scalar(select(func.count(SupportTicket.id)).where(SupportTicket.status == TicketStatus.OPEN)) or 0
    unread_threads = await db.scalar(select(func.count(EmailThread.id)).where(EmailThread.status == EmailThreadStatus.UNREAD)) or 0

    return {
        "total_merchants": total_merchants,
        "new_merchants_today": new_merchants_today,
        "total_stores": total_stores,
        "active_stores": active_stores,
        "total_staff": total_staff,
        "total_products": total_products,
        "total_transactions": sales_row.total_transactions if sales_row else 0,
        "total_gmv": int(sales_row.total_gmv) if sales_row else 0,
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
