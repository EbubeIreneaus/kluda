from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.user import User
from schemas.user import UserStatus
from libs.security import hash_password
from setting import settings


async def create_super_user(db: AsyncSession) -> User:
    res = await db.execute(
        select(User).where(User.email == settings.SUPER_STAFF_EMAIL)
    )
    existing_user = res.scalar_one_or_none()

    if existing_user:
        return existing_user

    super_user = User(
        fullname=settings.SUPER_STAFF_NAME or "Super Admin",
        email=settings.SUPER_STAFF_EMAIL,
        password=hash_password(settings.SUPER_STAFF_PASSWORD or "Password123!"),
        status=UserStatus.ACTIVE,
    )

    db.add(super_user)
    await db.flush()
    return super_user
