from schemas.business import StoreResponseMini
from schemas.business import StoreStatus
from models.business import Store
import uuid
from schemas.user import UserResponseMini
from datetime import timezone
from sqlalchemy.orm import selectinload
from datetime import datetime
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.config import get_db
from models.user import User, UserSession, StoreMember
from models.admin.user import Admin, AdminSession
from schemas.user import StaffPermission, StaffStatus, UserStatus
from schemas.admin.user import AdminPermission, AdminStatus, AdminRole
from libs.security import decode_access_token, get_client_ip, parse_device_info

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


async def get_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    raw_token = request.cookies.get("user_access_token") or request.cookies.get("staff_access_token")
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

    if not session or not session.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User session not found or expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = session.user
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is suspended or inactive",
        )

    return user

get_staff = get_current_user
get_user = get_current_user


async def get_optional_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    try:
        return await get_current_user(request, token, db)
    except Exception:
        return None


def require_permission(permission: StaffPermission | str):
    async def permission_checker(
        user: User = Depends(get_current_user),
    ) -> User:
        return user

    return permission_checker


async def get_staff_store(
    store_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> StoreResponseMini:
    try:
        req_store_id = uuid.UUID(str(store_id)) if not isinstance(store_id, uuid.UUID) else store_id
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid store ID format"
        )

    store = await db.scalar(
        select(Store).where(Store.store_id == req_store_id)
    )
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found"
        )

    if store.status != StoreStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Store is inactive and cannot be managed."
        )

    if store.user_id == user.user_id:
        return store

    from models.user import StoreMember
    member = await db.scalar(
        select(StoreMember).where(
            StoreMember.store_id == req_store_id,
            StoreMember.user_id == user.user_id,
            StoreMember.status == StaffStatus.ACTIVE
        )
    )
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: user does not belong to this store"
        )

    return store

get_store = get_staff_store


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


def require_superadmin():
    async def dependency(admin: Admin = Depends(get_admin)) -> Admin:
        if (
            admin.role in (AdminRole.SUPER_ADMIN, AdminRole.ADMIN)
            or AdminPermission.MANAGE_ALL in admin.permission
            or AdminPermission.MANAGE_ALL.value in admin.permission
        ):
            return admin
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin privileges required for this action",
        )
    return dependency