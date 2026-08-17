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
from schemas.user import StaffPermission, StaffStatus, UserStatus
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
    
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(StaffSession)
        .options(selectinload(StaffSession.staff))
        .where(StaffSession.session_id == session_id, StaffSession.expired_at > now)
    )

    session = result.scalar_one_or_none()

    if not session:
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

        # Admin role has full access to all endpoints
        if getattr(staff, "role", "").lower() == "admin":
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
            for p in staff_perm:
                val = p.value if hasattr(p, "value") else str(p)
                if val in ["manage:all", "*", "all", perm_value]:
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
    now = datetime.now(timezone.utc)

    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload structure",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(
        select(UserSession)
        .options(selectinload(UserSession.user))
        .where(
            UserSession.session_id == session_id,
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
    staff: StaffResponse = Depends(get_staff)
) -> StoreResponseMini:
    store = await db.scalar(
        select(Store).where(
           Store.store_id == staff.store_id
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