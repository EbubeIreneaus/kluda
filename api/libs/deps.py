from schemas.user import StaffResponse
from schemas.business import StoreResponseMini
from schemas.business import StoreStatus
from models.business import Store
import uuid
from schemas.user import UserResponseMini
from models import StaffSession
from datetime import timezone
from sqlalchemy.orm import selectinload
from datetime import datetime
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.config import get_db
from models.user import Staff, User, UserSession
from models.admin.user import Admin, AdminSession
from schemas.user import StaffPermission, StaffStatus, UserStatus
from schemas.admin.user import AdminPermission, AdminStatus, AdminRole
from libs.security import decode_access_token, get_client_ip, parse_device_info

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


async def get_staff(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Staff:
    raw_token = request.cookies.get("staff_access_token")
    if not raw_token and token:
        raw_token = token
    if not raw_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            raw_token = auth_header.split(" ")[1]

    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(raw_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    session_id = payload.get("session_id")
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload structure",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        session_uuid = uuid.UUID(str(session_id))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload structure",
            headers={"WWW-Authenticate": "Bearer"},
        )

    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(StaffSession)
        .options(selectinload(StaffSession.staff))
        .where(StaffSession.session_id == session_uuid, StaffSession.expired_at > now)
    )

    session = result.scalar_one_or_none()

    if not session:
        user_sess_res = await db.execute(
            select(UserSession)
            .options(selectinload(UserSession.user))
            .where(
                UserSession.session_id == session_uuid,
                UserSession.expired_at > now,
                UserSession.active == True,
            )
        )
        user_sess = user_sess_res.scalar_one_or_none()
        if user_sess and user_sess.user and user_sess.user.status == UserStatus.ACTIVE:
            owner_user = user_sess.user
            parts = (owner_user.fullname or "Owner").split()
            owner_staff = Staff(
                staff_id="OWNER",
                first_name=parts[0],
                last_name=parts[-1] if len(parts) > 1 else "",
                role="owner",
                email=owner_user.email,
                permission=[StaffPermission.RECORD_SALES.value, StaffPermission.VIEW_PRODUCT.value, StaffPermission.MANAGE_PRODUCT.value, StaffPermission.MANAGE_STAFF.value, StaffPermission.MANAGE_USER.value, StaffPermission.VIEW_ANALYTICS.value, "manage:all"],
                status=StaffStatus.ACTIVE,
                store_id=None,
                created_at=getattr(owner_user, "created_at", None),
                pin_hash=getattr(owner_user, "pin_hash", None),
                pin_salt=getattr(owner_user, "pin_salt", None),
            )
            setattr(owner_staff, "user_id", owner_user.user_id)
            setattr(owner_staff, "pin_hash", getattr(owner_user, "pin_hash", None))
            setattr(owner_staff, "pin_salt", getattr(owner_user, "pin_salt", None))
            return owner_staff

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Staff session not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    staff = session.staff
    staff_status_val = (
        staff.status.value if hasattr(staff.status, "value") else str(staff.status)
    )
    if staff_status_val in [
        StaffStatus.SUSPENDED.value,
        StaffStatus.TERMINATED.value,
        "suspended",
        "terminated",
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff account is suspended or terminated",
        )

    return staff


def require_permission(permission: StaffPermission | str):
    async def permission_checker(staff: Staff = Depends(get_staff)) -> Staff:
        perm_value = (
            permission.value
            if isinstance(permission, StaffPermission)
            else str(permission)
        )

        if (getattr(staff, "role", None) or "").lower() in ["admin", "manager", "owner"]:
            return staff

        staff_perm = staff.permission
        if not staff_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required permission: {perm_value}",
            )

        if isinstance(staff_perm, str):
            if staff_perm in ["manage:all", "all", perm_value]:
                return staff
            try:
                import json

                parsed = json.loads(staff_perm)
                if isinstance(parsed, list):
                    staff_perm = parsed
                elif isinstance(parsed, str) and parsed in [
                    "manage:all",
                    "*",
                    "all",
                    perm_value,
                ]:
                    return staff
            except Exception:
                staff_perm = [staff_perm]

        if isinstance(staff_perm, list):
            perms_str = [p.value if hasattr(p, "value") else str(p) for p in staff_perm]
            if "manage:all" in perms_str or "*" in perms_str or "all" in perms_str or perm_value in perms_str:
                return staff
            if perm_value == StaffPermission.VIEW_PRODUCT.value and StaffPermission.MANAGE_PRODUCT.value in perms_str:
                return staff

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied. Required permission: {perm_value}",
        )

    return permission_checker


async def get_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> UserResponseMini:
    raw_token = request.cookies.get("user_access_token")
    if not raw_token and token:
        raw_token = token
    if not raw_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            raw_token = auth_header.split(" ")[1]

    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(raw_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    session_id = payload.get("session_id")
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload structure",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        session_uuid = uuid.UUID(str(session_id))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload structure",
            headers={"WWW-Authenticate": "Bearer"},
        )

    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(UserSession)
        .options(selectinload(UserSession.user))
        .where(
            UserSession.session_id == session_uuid,
            UserSession.expired_at > now,
            UserSession.active == True,
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or expired session",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = session.user

    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="user account is inactive, contact suport for more info",
        )

    return user


async def get_store(
    store_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: UserResponseMini = Depends(get_user)
) -> StoreResponseMini:
    store = await db.scalar(
        select(Store).where(
          Store.store_id == store_id, Store.user_id == user.user_id
        )
    )

    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found under user account"
        )

    if store.status != StoreStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Store is inactive and cannot be managed."
        )
    
    return store

async def get_staff_store(
    store_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    staff: Staff = Depends(get_staff)
) -> StoreResponseMini:
    try:
        req_store_id = uuid.UUID(str(store_id)) if not isinstance(store_id, uuid.UUID) else store_id
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid store ID format"
        )

    if staff.role == "owner" or getattr(staff, "user_id", None):
        owner_user_id = getattr(staff, "user_id", None)
        stmt = select(Store).where(Store.store_id == req_store_id)
        if owner_user_id:
            stmt = stmt.where(Store.user_id == owner_user_id)
        store = await db.scalar(stmt)
        if not store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Store not found under owner account"
            )
    else:
        if not staff.store_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: staff is not assigned to any store"
            )
        try:
            staff_store_id = uuid.UUID(str(staff.store_id)) if not isinstance(staff.store_id, uuid.UUID) else staff.store_id
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid store ID assigned to staff"
            )

        if staff_store_id != req_store_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: staff does not belong to this store"
            )

        store = await db.scalar(
            select(Store).where(
               Store.store_id == req_store_id
            )
        )
        if not store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Store not found under staff account"
            )

    if store.status != StoreStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Store is inactive and cannot be managed."
        )
    
    return store


async def get_admin(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Admin:
    raw_token = request.cookies.get("admin_access_token")
    if not raw_token and token:
        raw_token = token
    if not raw_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            raw_token = auth_header.split(" ")[1]

    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(raw_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    session_id = payload.get("session_id")
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload structure",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        session_uuid = uuid.UUID(str(session_id))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload structure",
            headers={"WWW-Authenticate": "Bearer"},
        )

    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(AdminSession)
        .options(selectinload(AdminSession.admin))
        .where(
            AdminSession.session_id == session_uuid,
            AdminSession.expired_at > now,
            AdminSession.active == True,
        )
    )
    session = result.scalar_one_or_none()

    if not session or not session.admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin session not found or has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    admin = session.admin
    if admin.status != AdminStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is suspended or inactive",
        )

    return admin


def require_admin_permission(permission: AdminPermission):
    async def dependency(admin: Admin = Depends(get_admin)) -> Admin:
        if admin.role == AdminRole.SUPER_ADMIN:
            return admin
        if AdminPermission.MANAGE_ALL.value in admin.permission or AdminPermission.MANAGE_ALL in admin.permission:
            return admin
        if permission.value in admin.permission or permission in admin.permission:
            return admin
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: {permission.value} required",
        )
    return dependency