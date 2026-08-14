import pytest
from unittest.mock import AsyncMock, MagicMock
from libs.init_db import create_super_staff
from setting import settings
from schemas.user import StaffPermission


@pytest.mark.anyio
async def test_create_super_staff_creates_new():
    db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_res

    staff = await create_super_staff(db)

    assert staff.email == settings.SUPER_STAFF_EMAIL
    assert staff.permission == [StaffPermission.MANAGE_ALL]
    assert db.add.called
