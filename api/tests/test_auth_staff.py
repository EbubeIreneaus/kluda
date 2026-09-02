import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, Request
from libs.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    parse_device_info,
    hash_token,
)
from schemas.user import StaffPermission, StaffStatus, UserStatus
from models.user import User, UserSession
from libs.deps import get_user, require_permission


def test_password_hashing():
    raw_pass = "SecurePass123!"
    hashed = hash_password(raw_pass)
    assert hashed != raw_pass
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_jwt_token_claims():
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(uuid.uuid4()),
        "last_login": now.isoformat(),
        "ipaddress": "192.168.1.50",
        "device": "Macintosh (macOS; Chrome 120.0.0)",
    }
    token = create_access_token(payload, expires_delta=timedelta(hours=13))
    decoded = decode_access_token(token)

    assert decoded["sub"] == payload["sub"]
    assert decoded["last_login"] == now.isoformat()
    assert decoded["ipaddress"] == "192.168.1.50"
    assert decoded["device"] == "Macintosh (macOS; Chrome 120.0.0)"
    assert "exp" in decoded


def test_parse_device_info():
    ua_chrome = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    device_str = parse_device_info(ua_chrome)
    assert "Windows" in device_str or "Chrome" in device_str

    empty_device = parse_device_info(None)
    assert empty_device == "Unknown Device"


def test_permission_enum():
    assert StaffPermission.MANAGE_STAFF.value == "manage:staff"
    assert StaffPermission.MANAGE_ALL.value == "manage:all"


@pytest.mark.anyio
async def test_get_user_expired_or_missing_session():
    session_id = uuid.uuid4()
    user_id = uuid.uuid4()
    token = create_access_token({"sub": str(user_id), "session_id": str(session_id)})

    db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_res

    request = MagicMock(spec=Request)
    request.headers = {}
    request.cookies = {}

    with pytest.raises(HTTPException) as exc_info:
        await get_user(request=request, token=token, db=db)
    
    assert exc_info.value.status_code == 401
    assert "session not found" in exc_info.value.detail.lower() or "expired" in exc_info.value.detail.lower()


@pytest.mark.anyio
async def test_get_user_suspended_account():
    session_id = uuid.uuid4()
    user_id = uuid.uuid4()
    token = create_access_token({"sub": str(user_id), "session_id": str(session_id)})

    user = User(
        user_id=user_id,
        fullname="Suspended User",
        email="suspended@example.com",
        password=hash_password("secret"),
        status=UserStatus.SUSPENDED
    )
    user_session = UserSession(
        session_id=session_id,
        user_id=user_id,
        refresh_token_hash=hash_token("ref1"),
        expired_at=datetime.now(timezone.utc) + timedelta(days=1),
        ip_address="10.0.0.1",
        user_agent="Chrome",
        active=True,
        user=user
    )

    db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = user_session
    db.execute.return_value = mock_res

    request = MagicMock(spec=Request)
    request.headers = {}
    request.cookies = {}

    with pytest.raises(HTTPException) as exc_info:
        await get_user(request=request, token=token, db=db)

    assert exc_info.value.status_code == 403
    assert "inactive" in exc_info.value.detail.lower() or "support" in exc_info.value.detail.lower()


@pytest.mark.anyio
async def test_require_permission():
    user = User(
        user_id=uuid.uuid4(),
        fullname="Test User",
        email="test@example.com",
        password="hash",
        status=UserStatus.ACTIVE
    )

    checker = require_permission(StaffPermission.MANAGE_STAFF)
    res = await checker(user=user)
    assert res == user
