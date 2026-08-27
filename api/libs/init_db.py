from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.user import Staff
from schemas.user import StaffPermission, StaffStatus
from libs.security import hash_password
from setting import settings


async def create_super_staff(db: AsyncSession) -> Staff:
    res = await db.execute(
        select(Staff).where(Staff.email == settings.SUPER_STAFF_EMAIL)
    )
    existing_staff = res.scalar_one_or_none()

    if existing_staff:
        return existing_staff

    super_staff = Staff(
        staff_id="STF0001",
        first_name=settings.SUPER_STAFF_NAME,
        last_name="SuperAdmin",
        email=settings.SUPER_STAFF_EMAIL,
        password=hash_password(settings.SUPER_STAFF_PASSWORD),
        role="superadmin",
        permission=[StaffPermission.MANAGE_ALL],
        status=StaffStatus.ACTIVE,
    )

    db.add(super_staff)
    await db.flush()
    return super_staff
