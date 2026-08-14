import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, Request
from libs.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    parse_device_info,
)
from schemas.user import StaffPermission, StaffStatus
from models.user import Staff
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
        "staff_id": "STF1001",
        "last_login": now.isoformat(),
        "ipaddress": "192.168.1.50",
        "device": "Macintosh (macOS; Chrome 120.0.0)",
    }
    token = create_access_token(payload, expires_delta=timedelta(hours=13))
    decoded = decode_access_token(token)

    assert decoded["staff_id"] == "STF1001"
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
async def test_get_user_ip_mismatch():
    now = datetime.now(timezone.utc)
    payload = {
        "staff_id": "STF1001",
        "last_login": now.isoformat(),
        "ipaddress": "10.0.0.1",
        "device": "Unknown Device",
    }
    token = create_access_token(payload)

    # Mock staff object
    staff = Staff(
        staff_id="STF1001",
        first_name="John",
        last_name="Doe",
        role="admin",
        email="john@example.com",
        password=hash_password("secret"),
        permission=StaffPermission.MANAGE_STAFF,
        status=StaffStatus.ACTIVE,
        last_login=now,
    )

    db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = staff
    db.execute.return_value = mock_res

    # Mock Request with different IP (10.0.0.2)
    request = MagicMock(spec=Request)
    request.headers = {}
    request.client.host = "10.0.0.2"

    with pytest.raises(HTTPException) as exc_info:
        await get_user(request=request, token=token, db=db)
    
    assert exc_info.value.status_code == 401
    assert "IP address mismatch" in exc_info.value.detail


@pytest.mark.anyio
async def test_get_user_device_mismatch():
    now = datetime.now(timezone.utc)
    ua_str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
    device_str = parse_device_info(ua_str)

    payload = {
        "staff_id": "STF1001",
        "last_login": now.isoformat(),
        "ipaddress": "10.0.0.1",
        "device": device_str,
    }
    token = create_access_token(payload)

    staff = Staff(
        staff_id="STF1001",
        first_name="John",
        last_name="Doe",
        role="admin",
        email="john@example.com",
        password=hash_password("secret"),
        permission=StaffPermission.MANAGE_STAFF,
        status=StaffStatus.ACTIVE,
        last_login=now,
    )

    db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = staff
    db.execute.return_value = mock_res

    # Request with different user-agent (iPhone Safari)
    request = MagicMock(spec=Request)
    request.headers = {"user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1"}
    request.client.host = "10.0.0.1"

    with pytest.raises(HTTPException) as exc_info:
        await get_user(request=request, token=token, db=db)

    assert exc_info.value.status_code == 401
    assert "Device/browser mismatch" in exc_info.value.detail


@pytest.mark.anyio
async def test_require_permission():
    staff_admin = Staff(
        staff_id="STF1001",
        permission=StaffPermission.MANAGE_STAFF,
        status=StaffStatus.ACTIVE,
    )
    staff_regular = Staff(
        staff_id="STF1002",
        permission=StaffPermission.MANAGE_USER,
        status=StaffStatus.ACTIVE,
    )

    checker = require_permission(StaffPermission.MANAGE_STAFF)

    # Admin should succeed
    res = await checker(staff=staff_admin)
    assert res == staff_admin

    # Regular staff without MANAGE_STAFF should raise 403
    with pytest.raises(HTTPException) as exc_info:
        await checker(staff=staff_regular)
    assert exc_info.value.status_code == 403
