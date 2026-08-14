from datetime import datetime, timezone, timedelta
import secrets
import hashlib
import jwt
from pwdlib import PasswordHash
from user_agents import parse
from fastapi import Request
from setting import settings

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return password_hash.verify(plain_password, hashed_password)
    except Exception:
        return False


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(32)


def get_cookie_settings() -> dict:
    is_prod = settings.APP_ENV.lower() == "production"
    domain = (
        f".{settings.DOMAIN_NAME.lstrip('.')}"
        if is_prod and settings.DOMAIN_NAME not in ["localhost", "127.0.0.1"]
        else None
    )
    return {
        "domain": domain,
        "secure": is_prod,
        "samesite": "lax",
        "httponly": True,
        "path": "/",
    }


def create_access_token(payload: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = payload.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(hours=1)
    to_encode.update({"exp": expire, "iat": now})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])


def parse_device_info(user_agent_str: str | None) -> str:
    if not user_agent_str:
        return "Unknown Device"
    ua = parse(user_agent_str)
    device_family = ua.device.family or "Unknown"
    os_family = ua.os.family or "Unknown"
    browser_family = ua.browser.family or "Unknown"
    browser_version = ua.browser.version_string or ""
    return f"{device_family} ({os_family}; {browser_family} {browser_version})".strip()


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "0.0.0.0"
