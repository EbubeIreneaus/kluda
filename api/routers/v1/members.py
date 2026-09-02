import hashlib
import uuid
import secrets
from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from sqlalchemy.orm import selectinload

from models.config import get_db
from models.user import User, StoreMember
from models.business import Store
from models.subscription import UserSubscription
from models.admin.plan import Plan
from schemas.business import StoreResponseMini
from schemas.user import (
    StaffCreate,
    StaffUpdate,
    StaffResponse,
    StaffPermission,
    StaffStatus,
    StaffSetPin,
)
from libs.security import hash_password
from libs.deps import require_permission, get_staff_store, get_current_user
from libs.ws_manager import manager as ws_manager

router = APIRouter(prefix="/{store_id}/staff", tags=["Store Members"])


def _format_member_response(member: StoreMember, user: User, store_id: uuid.UUID) -> dict:
    parts = (user.fullname or "Member").split()
    return {
        "staff_id": str(user.user_id),
        "store_id": str(store_id),
        "first_name": parts[0],
        "last_name": parts[-1] if len(parts) > 1 else "",
        "other_name": None,
        "role": member.role,
        "email": user.email,
        "phone": user.phone,
        "permission": member.permission or [],
        "status": member.status.value if hasattr(member.status, "value") else str(member.status),
        "has_pin": bool(user.pin_hash),
        "created_at": member.created_at.isoformat() if member.created_at else None,
    }


@router.post("/pin")
async def set_my_pin(
    payload: StaffSetPin,
    store_id: uuid.UUID,
    store: StoreResponseMini = Depends(get_staff_store),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not payload.pin.isdigit():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="PIN must contain only numbers")

    salt = secrets.token_hex(16)
    pin_hash = hashlib.sha256((payload.pin + salt).encode()).hexdigest()

    user = await db.scalar(select(User).where(User.user_id == current_user.user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User record not found")

    user.pin_salt = salt
    user.pin_hash = pin_hash
    await db.commit()

    return {
        "status": "ok",
        "success": True,
        "message": "PIN updated successfully",
        "has_pin": True,
        "pin_hash": pin_hash,
        "pin_salt": salt,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
@router.post("/", status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def create_staff(
    staff_data: StaffCreate,
    store_id: uuid.UUID,
    store: StoreResponseMini = Depends(get_staff_store),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(StaffPermission.MANAGE_STAFF)),
):
    db_store = await db.scalar(select(Store).where(Store.store_id == store.store_id))
    owner_user_id = db_store.user_id if db_store else None
    owner = await db.scalar(select(User).where(User.user_id == owner_user_id)) if owner_user_id else None
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

    staff_limits = {"free": 2, "trial": 5, "growth": 20, "enterprise": 0}
    staff_limit = staff_limits.get(plan.slug, 2) if plan else 2

    if staff_limit > 0 and owner_user_id:
        total_staff = (
            await db.scalar(
                select(func.count(StoreMember.id))
                .join(Store, StoreMember.store_id == Store.store_id)
                .where(
                    Store.user_id == owner_user_id,
                    StoreMember.role != "owner",
                    StoreMember.status == StaffStatus.ACTIVE,
                )
            )
        ) or 0
        if total_staff >= staff_limit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Staff limit reached ({staff_limit} cashiers/staff). Upgrade your subscription plan to add more staff members.",
            )

    clean_email = staff_data.email.lower().strip()
    user_rec = await db.scalar(select(User).where(func.lower(User.email) == clean_email))

    if user_rec:
        if not user_rec.phone and staff_data.phone:
            user_rec.phone = staff_data.phone
    else:
        random_pw = secrets.token_urlsafe(16)
        user_rec = User(
            fullname=f"{staff_data.first_name} {staff_data.last_name}".strip(),
            email=clean_email,
            phone=staff_data.phone,
            password=hash_password(random_pw),
        )
        db.add(user_rec)
        await db.flush()

    existing_member = await db.scalar(
        select(StoreMember).where(
            StoreMember.store_id == store.store_id,
            StoreMember.user_id == user_rec.user_id,
        )
    )

    if existing_member:
        existing_member.status = staff_data.status
        existing_member.role = staff_data.role
        existing_member.permission = [
            p.value if hasattr(p, "value") else str(p) for p in staff_data.permission
        ]
        existing_member.display_name = f"{staff_data.first_name} {staff_data.last_name}".strip()
        await db.commit()
        await db.refresh(existing_member)
        return _format_member_response(existing_member, user_rec, store.store_id)

    member_rec = StoreMember(
        store_id=store.store_id,
        user_id=user_rec.user_id,
        role=staff_data.role,
        display_name=f"{staff_data.first_name} {staff_data.last_name}".strip(),
        permission=[
            p.value if hasattr(p, "value") else str(p) for p in staff_data.permission
        ],
        status=staff_data.status,
    )
    db.add(member_rec)
    await db.commit()
    await db.refresh(member_rec)

    return _format_member_response(member_rec, user_rec, store.store_id)


@router.get("")
@router.get("/", include_in_schema=False)
async def get_staffs(
    store_id: uuid.UUID,
    status_filter: StaffStatus | None = Query(None, alias="status"),
    store: StoreResponseMini = Depends(get_staff_store),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(StaffPermission.MANAGE_STAFF)),
):
    query = (
        select(StoreMember)
        .options(selectinload(StoreMember.user))
        .where(StoreMember.store_id == store.store_id)
    )
    if status_filter:
        query = query.where(StoreMember.status == status_filter)

    members = (await db.scalars(query)).all()
    return [_format_member_response(m, m.user, store.store_id) for m in members if m.user]


@router.get("/{staff_id}")
async def get_staff_detail(
    staff_id: str,
    store_id: uuid.UUID,
    store: StoreResponseMini = Depends(get_staff_store),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(StaffPermission.MANAGE_STAFF)),
):
    try:
        user_uuid = uuid.UUID(staff_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid staff ID format")

    member = await db.scalar(
        select(StoreMember)
        .options(selectinload(StoreMember.user))
        .where(StoreMember.store_id == store.store_id, StoreMember.user_id == user_uuid)
    )
    if not member or not member.user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff member not found")

    return _format_member_response(member, member.user, store.store_id)


@router.put("/{staff_id}")
@router.patch("/{staff_id}")
async def update_staff(
    staff_id: str,
    update_data: StaffUpdate,
    store_id: uuid.UUID,
    store: StoreResponseMini = Depends(get_staff_store),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(StaffPermission.MANAGE_STAFF)),
):
    try:
        user_uuid = uuid.UUID(staff_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid staff ID format")

    member = await db.scalar(
        select(StoreMember)
        .options(selectinload(StoreMember.user))
        .where(StoreMember.store_id == store.store_id, StoreMember.user_id == user_uuid)
    )
    if not member or not member.user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff member not found")

    if update_data.role:
        member.role = update_data.role
    if update_data.status:
        member.status = update_data.status
    if update_data.permission is not None:
        member.permission = [
            p.value if hasattr(p, "value") else str(p) for p in update_data.permission
        ]
    if update_data.first_name or update_data.last_name:
        fn = update_data.first_name or ""
        ln = update_data.last_name or ""
        member.display_name = f"{fn} {ln}".strip()

    await db.commit()
    await db.refresh(member)

    await ws_manager.broadcast(
        store.store_id,
        {
            "event": "staff_status_changed",
            "data": {
                "staff_id": staff_id,
                "status": member.status.value if hasattr(member.status, "value") else str(member.status),
                "role": member.role,
                "permission": member.permission,
            },
        },
    )

    return _format_member_response(member, member.user, store.store_id)


@router.delete("/{staff_id}")
async def delete_staff(
    staff_id: str,
    store_id: uuid.UUID,
    store: StoreResponseMini = Depends(get_staff_store),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(StaffPermission.MANAGE_STAFF)),
):
    try:
        user_uuid = uuid.UUID(staff_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid staff ID format")

    member = await db.scalar(
        select(StoreMember).where(StoreMember.store_id == store.store_id, StoreMember.user_id == user_uuid)
    )
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff member not found")

    member.status = StaffStatus.TERMINATED
    await db.commit()

    await ws_manager.broadcast(
        store.store_id,
        {
            "event": "staff_status_changed",
            "data": {
                "staff_id": staff_id,
                "status": "terminated",
            },
        },
    )

    return {"message": f"Staff member '{staff_id}' has been removed from this store"}
