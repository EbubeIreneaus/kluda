import uuid
import random
import string
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from models.config import get_db
from models.user import User
from models.business import Store
from models.admin.user import Admin
from schemas.admin.merchant import AdminMerchantListItem, AdminMerchantDetailResponse, AdminMerchantStatusUpdateRequest
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
        stmt = stmt.where(User.status == status_filter)

    stmt = stmt.order_by(User.created_at.desc()).limit(limit).offset(offset)
    users = (await db.scalars(stmt)).all()

    items = []
    for u in users:
        store_count = await db.scalar(select(func.count(Store.id)).where(Store.user_id == u.user_id)) or 0
        items.append(
            AdminMerchantListItem(
                id=u.id,
                user_id=u.user_id,
                fullname=u.fullname,
                email=u.email,
                phone=u.phone,
                status=u.status.value if hasattr(u.status, 'value') else str(u.status),
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
    user = await db.scalar(select(User).where(User.user_id == user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant not found")

    stores = (await db.scalars(select(Store).where(Store.user_id == user.user_id))).all()
    stores_data = [
        {"store_id": str(s.store_id), "name": s.name, "status": str(s.status.value if hasattr(s.status, 'value') else s.status)}
        for s in stores
    ]

    return AdminMerchantDetailResponse(
        id=user.id,
        user_id=user.user_id,
        fullname=user.fullname,
        email=user.email,
        phone=user.phone,
        status=user.status.value if hasattr(user.status, 'value') else str(user.status),
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

    old_status = user.status.value if hasattr(user.status, 'value') else str(user.status)
    user.status = UserStatus(payload.status) if payload.status in [s.value for s in UserStatus] else payload.status
    await db.flush()

    await record_audit_log(
        db=db,
        admin_id=admin.admin_id,
        action="MERCHANT_STATUS_UPDATED",
        target_type="user",
        target_id=user.user_id,
        details={"old_status": old_status, "new_status": payload.status, "reason": payload.reason},
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
