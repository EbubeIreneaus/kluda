import uuid
import random
import string
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from models.config import get_db
from models.user import User, StoreMember
from models.business import Store
from models.stock import Stock, Sale
from models.subscription import UserSubscription
from models.admin.user import Admin
from schemas.admin.merchant import (
    AdminMerchantListItem,
    AdminMerchantDetailResponse,
    AdminMerchantStatusUpdateRequest,
    AdminMerchantSubscriptionInfo,
    AdminMerchantStoreSummary,
)
from schemas.admin.user import AdminPermission
from schemas.user import UserStatus
from libs.deps import require_admin_permission
from libs.audit import record_audit_log
from libs.resend import resend_client
from setting import settings


router = APIRouter(prefix="/merchants", tags=["Admin Merchant Management"])


@router.get("", response_model=list[AdminMerchantListItem])
async def list_merchants(
    search: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_admin_permission(AdminPermission.MANAGE_USERS)),
):
    stmt = select(User)
    if search:
        stmt = stmt.where((User.fullname.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%")))
    if status_filter:
        target_filter = status_filter.lower()
        try:
            stmt = stmt.where(User.status == UserStatus(target_filter))
        except ValueError:
            stmt = stmt.where(User.status == target_filter)

    stmt = stmt.order_by(User.created_at.desc()).limit(limit).offset(offset)
    users = (await db.scalars(stmt)).all()

    items = []
    for u in users:
        store_count = await db.scalar(select(func.count(Store.id)).where(Store.user_id == u.user_id)) or 0
        status_str = (u.status.value if hasattr(u.status, 'value') else str(u.status)).lower()
        items.append(
            AdminMerchantListItem(
                id=u.id,
                user_id=u.user_id,
                fullname=u.fullname,
                email=u.email,
                phone=u.phone,
                status=status_str,
                store_count=store_count,
                created_at=u.created_at,
            )
        )
    return items


@router.get("/{user_id}", response_model=AdminMerchantDetailResponse)
async def get_merchant_detail(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_admin_permission(AdminPermission.MANAGE_USERS)),
):
    user = await db.scalar(
        select(User)
        .options(
            selectinload(User.current_subscription).selectinload(UserSubscription.plan)
        )
        .where(User.user_id == user_id)
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant not found")

    subscription_info = None
    if user.current_subscription:
        cur_sub = user.current_subscription
        plan_slug = cur_sub.plan_id
        plan_name = cur_sub.plan.name if cur_sub.plan else cur_sub.plan_id
        interval = cur_sub.plan.interval if cur_sub.plan else None
        subscription_info = AdminMerchantSubscriptionInfo(
            plan_slug=plan_slug,
            plan_name=plan_name,
            interval=interval,
            status=cur_sub.status.value if hasattr(cur_sub.status, "value") else str(cur_sub.status),
            amount=cur_sub.amount,
            is_trial=cur_sub.is_trial,
            next_renewal=cur_sub.next_renewal,
        )

    stores = (
        await db.scalars(
            select(Store).where(Store.user_id == user.user_id).order_by(Store.created_at.desc())
        )
    ).all()

    stores_data: list[AdminMerchantStoreSummary] = []
    for s in stores:
        staff_count = await db.scalar(select(func.count(StoreMember.id)).where(StoreMember.store_id == s.store_id)) or 0
        product_count = await db.scalar(select(func.count(Stock.id)).where(Stock.store_id == s.store_id)) or 0
        sales_stats = await db.execute(
            select(
                func.count(Sale.id).label("total_sales"),
                func.coalesce(func.sum(Sale.amount_recived), 0).label("total_rev")
            ).where(Sale.store_id == s.store_id)
        )
        stats_row = sales_stats.first()
        stores_data.append(
            AdminMerchantStoreSummary(
                store_id=s.store_id,
                name=s.name,
                category=s.category,
                status=s.status.value if hasattr(s.status, "value") else str(s.status),
                staff_count=staff_count,
                product_count=product_count,
                total_sales_count=stats_row.total_sales if stats_row else 0,
                total_revenue=int(stats_row.total_rev) if stats_row else 0,
                created_at=s.created_at,
            )
        )

    return AdminMerchantDetailResponse(
        id=user.id,
        user_id=user.user_id,
        fullname=user.fullname,
        email=user.email,
        phone=user.phone,
        status=(user.status.value if hasattr(user.status, 'value') else str(user.status)).lower(),
        subscription=subscription_info,
        stores=stores_data,
        created_at=user.created_at,
        last_login=user.last_login,
    )


@router.put("/{user_id}/status")
async def update_merchant_status(
    user_id: uuid.UUID,
    payload: AdminMerchantStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_admin_permission(AdminPermission.MANAGE_USERS)),
):
    user = await db.scalar(select(User).where(User.user_id == user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant not found")

    old_status = (user.status.value if hasattr(user.status, 'value') else str(user.status)).lower()
    target_status = payload.status.lower()
    try:
        user.status = UserStatus(target_status)
    except ValueError:
        user.status = UserStatus.ACTIVE if target_status == "active" else UserStatus.SUSPENDED

    await db.flush()

    await record_audit_log(
        db=db,
        admin_id=admin.admin_id,
        action="MERCHANT_STATUS_UPDATED",
        target_type="user",
        target_id=user.user_id,
        details={"old_status": old_status, "new_status": target_status, "reason": payload.reason},
    )
    return {"status": "ok", "message": "Merchant status updated successfully"}


@router.post("/{user_id}/reset-password")
async def trigger_merchant_password_reset(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_admin_permission(AdminPermission.MANAGE_USERS)),
):
    user = await db.scalar(select(User).where(User.user_id == user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant not found")

    otp = "".join(random.choices(string.digits, k=6))
    now = datetime.now(timezone.utc)
    user.otp_token = otp
    user.otp_expires_at = now + timedelta(minutes=30)
    await db.flush()

    if hasattr(settings, "RESEND_API_KEY") and settings.RESEND_API_KEY:
        try:
            resend_client.Emails.send({
                "from": f"Kluda Support <support@{settings.DOMAIN_NAME}>",
                "to": [user.email],
                "subject": "Password Reset Assistance",
                "html": f"<p>Hello {user.fullname},</p><p>An administrator has initiated a password reset for your account. Your reset code is <strong>{otp}</strong>.</p>",
            })
        except Exception:
            pass

    await record_audit_log(
        db=db,
        admin_id=admin.admin_id,
        action="MERCHANT_PASSWORD_RESET_TRIGGERED",
        target_type="user",
        target_id=user.user_id,
    )
    return {"status": "ok", "message": "Password reset code sent to merchant"}
