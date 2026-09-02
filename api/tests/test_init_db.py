import pytest
from unittest.mock import AsyncMock, MagicMock
from libs.init_db import create_super_user
from setting import settings


@pytest.mark.anyio
async def test_create_super_user_creates_new():
    db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_res

    user = await create_super_user(db)

    assert user.email == settings.SUPER_STAFF_EMAIL
    assert db.add.called
