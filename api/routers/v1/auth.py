from datetime import datetime, timezone, timedelta
import uuid
import secrets
from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends, status, Request, Response, Cookie, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from models.config import get_db
from models.user import User, UserSession, StoreMember
from models.subscription import UserSubscription
from schemas.subscription import SubscriptionStatus, PaymentChannel
from schemas.business import StoreStatus
from models.business import Store
from schemas.user import (
    ChangePasswordRequest,
    PasswordResetEmailRequest,
    PasswordResetVerifyRequest,
    PasswordResetSubmitRequest,
    UserStatus,
    UserLogin,
    UserCreate,
    UserRegisterWithStore,
    UserResponseMini,
    StaffStatus,
)
from libs.deps import get_user, get_current_user
from libs.security import (
    verify_password,
    hash_password,
    create_access_token,
    hash_token,
    generate_refresh_token,
    get_cookie_settings,
    get_client_ip,
)

from libs.cache import get_cache, set_cache

router = APIRouter(prefix="/auth", tags=["Auth"])

CACHE_KEY_CONTACT_INFO = "kluda:cache:public_contact_info"


@router.get("/contact-info")
async def get_public_contact_info(db: AsyncSession = Depends(get_db)):
    cached = await get_cache(CACHE_KEY_CONTACT_INFO)
    if cached is not None:
        return cached

    from models.admin.setting import SystemSetting
    setting = await db.scalar(select(SystemSetting).where(SystemSetting.key == "platform_contact_info"))
    result_val = setting.value if (setting and setting.value) else {}
    await set_cache(CACHE_KEY_CONTACT_INFO, result_val, expire_seconds=86400)
    return result_val


async def generate_user_id(db: AsyncSession) -> uuid.UUID:
    id = uuid.uuid4()
    return id


async def get_user_stores(user_id: uuid.UUID, db: AsyncSession) -> list[dict]:
    owned_stores = (
        await db.scalars(
            select(Store).where(
                Store.user_id == user_id,
                Store.status != StoreStatus.DELETED,
            )
        )
    ).all()

    store_items = []
    seen_ids = set()

    for s in owned_stores:
        seen_ids.add(s.store_id)
        store_items.append({
            "store_id": str(s.store_id),
            "name": s.name,
            "category": s.category,
            "address": s.address,
            "phone": getattr(s, "phone", None),
            "role": "owner",
            "is_owner": True,
            "display_name": None,
            "permission": ["manage:all"]
        })

    memberships = (
        await db.scalars(
            select(StoreMember)
            .options(selectinload(StoreMember.store))
            .where(StoreMember.user_id == user_id, StoreMember.status == StaffStatus.ACTIVE)
        )
    ).all()

    for m in memberships:
        if m.store and m.store.store_id not in seen_ids and m.store.status != StoreStatus.DELETED:
            seen_ids.add(m.store.store_id)
            store_items.append({
                "store_id": str(m.store.store_id),
                "name": m.store.name,
                "category": m.store.category,
                "address": m.store.address,
                "phone": getattr(m.store, "phone", None),
                "role": m.role,
                "is_owner": False,
                "display_name": m.display_name,
                "permission": m.permission or []
            })

    return store_items


def _make_staff_compatibility_dict(user: User, stores: list[dict]) -> dict:
    parts = (user.fullname or "User").split()
    primary = stores[0] if stores else None
    return {
        "staff_id": str(user.user_id),
        "store_id": primary["store_id"] if primary else None,
        "first_name": parts[0],
        "last_name": parts[-1] if len(parts) > 1 else "",
        "other_name": None,
        "role": primary["role"] if primary else "owner",
        "email": user.email,
        "phone": user.phone,
        "permission": primary["permission"] if primary else ["manage:all"],
        "status": user.status.value if hasattr(user.status, "value") else str(user.status),
        "has_pin": bool(getattr(user, "pin_hash", None)),
        "referral_code": getattr(user, "referral_code", None),
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


async def generate_user_referral_code(db: AsyncSession, fullname: str) -> str:
    clean_name = "".join(c for c in fullname if c.isalnum())[:5].upper() or "KLUDA"
    for _ in range(10):
        code = f"{clean_name}-{secrets.token_hex(3).upper()}"
        exists = await db.scalar(select(func.count(User.id)).where(User.referral_code == code))
        if not exists:
            return code
    return f"KLUDA-{uuid.uuid4().hex[:6].upper()}"


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserRegisterWithStore,
    request: Request,
    response: Response,
    user_agent: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db),
):
    email = body.email.lower().strip()
    email_check = await db.execute(select(User).where(func.lower(User.email) == email))
    if email_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    user_id = await generate_user_id(db)
    my_referral_code = await generate_user_referral_code(db, body.fullname)

    referred_by_id = None
    if body.referral_code:
        ref_clean = body.referral_code.strip().upper()
        ref_user = await db.scalar(select(User).where(func.upper(User.referral_code) == ref_clean))
        if ref_user:
            referred_by_id = ref_user.id
    
    new_user = User(
        fullname=body.fullname,
        email=email,
        phone=body.phone,
        user_id=user_id,
        password=hash_password(body.password),
        referral_code=my_referral_code,
        referred_by_id=referred_by_id,
    )

    db.add(new_user)
    await db.flush()

    # Fresh users start with free tier
    now = datetime.now(timezone.utc)
    free_sub = UserSubscription(
        user_id=new_user.user_id,
        plan_id="free",
        status=SubscriptionStatus.ACTIVE,
        amount=0,
        payment_channel=PaymentChannel.PAYSTACK,
        next_renewal=now + timedelta(days=36500),
        idempotency_key=f"init_free_{new_user.user_id}",
    )
    db.add(free_sub)
    await db.flush()
    new_user.current_subscription_id = free_sub.subscription_id

    store_obj = None
    if body.store_name:
        store_obj = Store(
            name=body.store_name,
            category=body.store_category or "Retail",
            address=body.store_address or "Main Branch",
            user_id=new_user.user_id,
            status=StoreStatus.ACTIVE
        )
        db.add(store_obj)
        await db.flush()

        member_entry = StoreMember(
            store_id=store_obj.store_id,
            user_id=new_user.user_id,
            role="owner",
            permission=["manage:all"],
            status=StaffStatus.ACTIVE
        )
        db.add(member_entry)
        await db.flush()

    now = datetime.now(timezone.utc)
    raw_refresh_token = generate_refresh_token()
    r_hash = hash_token(raw_refresh_token)
    access_token_expired_at = now + timedelta(hours=1)
    refresh_token_expired_at = now + timedelta(days=30)
    client_ip = get_client_ip(request)

    new_session = UserSession(
        user_id=new_user.user_id,
        refresh_token_hash=r_hash,
        ip_address=client_ip,
        user_agent=user_agent,
        expired_at=refresh_token_expired_at,
    )
    db.add(new_session)
    await db.flush()

    payload = {
        "sub": str(new_user.user_id),
        "session_id": str(new_session.session_id),
    }

    access_token = create_access_token(payload, expires_delta=timedelta(hours=1))
    cookie_cfg = get_cookie_settings()

    response.set_cookie(
        "user_access_token",
        access_token,
        expires=access_token_expired_at,
        max_age=3600,
        **cookie_cfg,
    )
    response.set_cookie(
        "staff_access_token",
        access_token,
        expires=access_token_expired_at,
        max_age=3600,
        **cookie_cfg,
    )
    response.set_cookie(
        "user_refresh_token",
        raw_refresh_token,
        expires=refresh_token_expired_at,
        max_age=30 * 24 * 3600,
        **cookie_cfg,
    )
    response.set_cookie(
        "staff_refresh_token",
        raw_refresh_token,
        expires=refresh_token_expired_at,
        max_age=30 * 24 * 3600,
        **cookie_cfg,
    )

    stores = await get_user_stores(new_user.user_id, db)
    staff_obj = _make_staff_compatibility_dict(new_user, stores)

    return {
        "success": True,
        "access_token": access_token,
        "user_access_token": access_token,
        "refresh_token": raw_refresh_token,
        "user_refresh_token": raw_refresh_token,
        "user": new_user,
        "staff": staff_obj,
        "store_id": staff_obj["store_id"],
        "stores": stores,
    }


@router.post("/login")
async def login_user(
    login_data: UserLogin,
    request: Request,
    response: Response,
    user_agent: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db),
):
    identifier = (login_data.email or login_data.staff_id or "").lower().strip()
    result = await db.execute(select(User).where(func.lower(User.email) == identifier))
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active. contact support for more details",
        )

    now = datetime.now(timezone.utc)
    user.last_login = now

    raw_refresh_token = generate_refresh_token()
    r_hash = hash_token(raw_refresh_token)
    access_token_expired_at = now + timedelta(hours=1)
    refresh_token_expired_at = now + timedelta(days=30)
    client_ip = get_client_ip(request)

    new_session = UserSession(
        user_id=user.user_id,
        refresh_token_hash=r_hash,
        ip_address=client_ip,
        user_agent=user_agent,
        expired_at=refresh_token_expired_at,
    )
    db.add(new_session)
    await db.flush()

    payload = {
        "sub": str(user.user_id),
        "session_id": str(new_session.session_id),
    }

    access_token = create_access_token(payload, expires_delta=timedelta(hours=1))
    cookie_cfg = get_cookie_settings()

    response.set_cookie(
        "user_access_token",
        access_token,
        expires=access_token_expired_at,
        max_age=3600,
        **cookie_cfg,
    )
    response.set_cookie(
        "staff_access_token",
        access_token,
        expires=access_token_expired_at,
        max_age=3600,
        **cookie_cfg,
    )
    response.set_cookie(
        "user_refresh_token",
        raw_refresh_token,
        expires=refresh_token_expired_at,
        max_age=30 * 24 * 3600,
        **cookie_cfg,
    )
    response.set_cookie(
        "staff_refresh_token",
        raw_refresh_token,
        expires=refresh_token_expired_at,
        max_age=30 * 24 * 3600,
        **cookie_cfg,
    )

    stores = await get_user_stores(user.user_id, db)
    staff_obj = _make_staff_compatibility_dict(user, stores)

    return {
        "success": True,
        "access_token": access_token,
        "user_access_token": access_token,
        "refresh_token": raw_refresh_token,
        "user_refresh_token": raw_refresh_token,
        "user": user,
        "staff": staff_obj,
        "store_id": staff_obj["store_id"],
        "stores": stores,
    }


@router.post("/refresh-token")
async def refresh_token_endpoint(
    request: Request,
    response: Response,
    user_refresh_token: Annotated[str | None, Cookie()] = None,
    db: AsyncSession = Depends(get_db),
):
    body_data = {}
    try:
        raw_body = await request.json()
        if isinstance(raw_body, dict):
            body_data = raw_body
    except Exception:
        pass

    if not user_refresh_token:
        user_refresh_token = request.cookies.get("staff_refresh_token")
    if not user_refresh_token:
        user_refresh_token = body_data.get("refresh_token") or body_data.get("user_refresh_token")
    if not user_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token",
        )

    r_hash = hash_token(user_refresh_token)
    stmt = (
        select(UserSession)
        .options(selectinload(UserSession.user))
        .where(
            UserSession.refresh_token_hash == r_hash,
            UserSession.active == True,
            UserSession.expired_at > datetime.now(timezone.utc),
        )
    )
    session = (await db.execute(stmt)).scalar_one_or_none()
    if not session or not session.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user = session.user
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is suspended or inactive",
        )

    client_app = request.headers.get("X-Client-App") or body_data.get("client_app")
    pin_proof = request.headers.get("X-Pin-Proof") or body_data.get("pin_proof")

    # In-memory Proof-of-Possession for POS terminals:
    # If the request originates from a POS client and user has configured a terminal PIN,
    # require the in-memory PIN proof to match user.pin_hash.
    if client_app == "pos" and user.pin_hash:
        if not pin_proof or pin_proof != user.pin_hash:
            session.active = False
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Terminal locked: Valid PIN proof required to refresh session",
            )

    now = datetime.now(timezone.utc)
    new_raw_refresh = generate_refresh_token()
    session.refresh_token_hash = hash_token(new_raw_refresh)
    session.expired_at = now + timedelta(days=30)
    session.ip_address = get_client_ip(request)

    access_token_expired_at = now + timedelta(hours=1)
    payload = {
        "sub": str(user.user_id),
        "session_id": str(session.session_id),
    }
    new_access_token = create_access_token(payload, expires_delta=timedelta(hours=1))
    cookie_cfg = get_cookie_settings()

    response.set_cookie(
        "user_access_token",
        new_access_token,
        expires=access_token_expired_at,
        max_age=3600,
        **cookie_cfg,
    )
    response.set_cookie(
        "staff_access_token",
        new_access_token,
        expires=access_token_expired_at,
        max_age=3600,
        **cookie_cfg,
    )
    response.set_cookie(
        "user_refresh_token",
        new_raw_refresh,
        expires=session.expired_at,
        max_age=30 * 24 * 3600,
        **cookie_cfg,
    )
    response.set_cookie(
        "staff_refresh_token",
        new_raw_refresh,
        expires=session.expired_at,
        max_age=30 * 24 * 3600,
        **cookie_cfg,
    )

    stores = await get_user_stores(user.user_id, db)
    staff_obj = _make_staff_compatibility_dict(user, stores)

    return {
        "success": True,
        "access_token": new_access_token,
        "user_access_token": new_access_token,
        "refresh_token": new_raw_refresh,
        "user": user,
        "staff": staff_obj,
        "store_id": staff_obj["store_id"],
        "stores": stores,
    }


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    user_refresh_token: Annotated[str | None, Cookie()] = None,
    db: AsyncSession = Depends(get_db),
):
    if not user_refresh_token:
        user_refresh_token = request.cookies.get("staff_refresh_token")
    if user_refresh_token:
        r_hash = hash_token(user_refresh_token)
        session = (
            await db.execute(
                select(UserSession).where(UserSession.refresh_token_hash == r_hash)
            )
        ).scalar_one_or_none()
        if session:
            session.active = False
            await db.flush()

    cookie_cfg = get_cookie_settings()
    response.delete_cookie("user_access_token", domain=cookie_cfg.get("domain"), path="/")
    response.delete_cookie("user_refresh_token", domain=cookie_cfg.get("domain"), path="/")
    response.delete_cookie("staff_access_token", domain=cookie_cfg.get("domain"), path="/")
    response.delete_cookie("staff_refresh_token", domain=cookie_cfg.get("domain"), path="/")
    return {"message": "Successfully logged out", "success": True}


@router.get("/me")
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stores = await get_user_stores(current_user.user_id, db)
    staff_obj = _make_staff_compatibility_dict(current_user, stores)
    return {
        "user_id": str(current_user.user_id),
        "fullname": current_user.fullname,
        "email": current_user.email,
        "phone": current_user.phone,
        "role": staff_obj["role"],
        "permission": staff_obj["permission"],
        "status": staff_obj["status"],
        "has_pin": staff_obj["has_pin"],
        "store_id": staff_obj["store_id"],
        "stores": stores,
        "staff": staff_obj,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
    }


@router.post("/change-password")
async def change_password(
    req: ChangePasswordRequest,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(req.old_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )

    current_user.password = hash_password(req.new_password)

    user_with_sessions = await db.scalar(
        select(User)
        .options(selectinload(User.sessions))
        .where(User.user_id == current_user.user_id)
    )
    if user_with_sessions:
        for s in user_with_sessions.sessions:
            s.active = False

    await db.flush()
    cookie_cfg = get_cookie_settings()
    response.delete_cookie("user_access_token", domain=cookie_cfg.get("domain"), path="/")
    response.delete_cookie("user_refresh_token", domain=cookie_cfg.get("domain"), path="/")
    response.delete_cookie("staff_access_token", domain=cookie_cfg.get("domain"), path="/")
    response.delete_cookie("staff_refresh_token", domain=cookie_cfg.get("domain"), path="/")

    return {
        "success": True,
        "message": "Password changed successfully. Please log in again.",
    }


@router.post("/password-reset/request")
async def request_password_reset(
    req: PasswordResetEmailRequest,
    db: AsyncSession = Depends(get_db),
):
    clean_email = req.email.strip().lower()
    user = (
        await db.execute(select(User).where(func.lower(User.email) == clean_email))
    ).scalar_one_or_none()

    if user and user.status == UserStatus.ACTIVE:
        otp = f"{secrets.randbelow(900000) + 100000}"
        user.reset_token = hash_token(otp)
        user.reset_token_expires = datetime.now(timezone.utc) + timedelta(minutes=15)
        await db.flush()
        try:
            from worker.config import get_arq_pool
            pool = await get_arq_pool()
            if pool:
                await pool.enqueue_job("send_auth_reset_email", clean_email, otp, "Store Account")
        except Exception:
            pass

    return {
        "success": True,
        "message": "If this email is registered, a reset code has been sent.",
    }


@router.post("/password-reset/verify")
async def verify_password_reset_code(
    req: PasswordResetVerifyRequest,
    db: AsyncSession = Depends(get_db),
):
    clean_email = req.email.strip().lower()
    user = (
        await db.execute(select(User).where(func.lower(User.email) == clean_email))
    ).scalar_one_or_none()

    code_val = (req.code or req.otp_token or "").strip()
    if (
        not user
        or not user.reset_token
        or not user.reset_token_expires
        or user.reset_token != hash_token(code_val)
        or user.reset_token_expires < datetime.now(timezone.utc)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset code",
        )

    return {"success": True, "message": "Reset code is valid"}


@router.post("/password-reset/submit")
async def submit_password_reset(
    req: PasswordResetSubmitRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    clean_email = req.email.strip().lower()
    user = (
        await db.execute(select(User).where(func.lower(User.email) == clean_email))
    ).scalar_one_or_none()

    code_val = (req.code or req.otp_token or "").strip()
    if (
        not user
        or not user.reset_token
        or not user.reset_token_expires
        or user.reset_token != hash_token(code_val)
        or user.reset_token_expires < datetime.now(timezone.utc)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset code",
        )

    user.password = hash_password(req.new_password)
    user.reset_token = None
    user.reset_token_expires = None

    user_with_sessions = await db.scalar(
        select(User)
        .options(selectinload(User.sessions))
        .where(User.user_id == user.user_id)
    )
    if user_with_sessions:
        for s in user_with_sessions.sessions:
            s.active = False

    await db.flush()
    cookie_cfg = get_cookie_settings()
    response.delete_cookie("user_access_token", domain=cookie_cfg.get("domain"), path="/")
    response.delete_cookie("user_refresh_token", domain=cookie_cfg.get("domain"), path="/")
    response.delete_cookie("staff_access_token", domain=cookie_cfg.get("domain"), path="/")
    response.delete_cookie("staff_refresh_token", domain=cookie_cfg.get("domain"), path="/")

    return {
        "success": True,
        "message": "Password reset successfully. Please log in with your new password.",
    }
