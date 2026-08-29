import asyncio
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select
from models.config import LocalSession
from models.admin.user import Admin
from schemas.admin.user import AdminRole, AdminPermission, AdminStatus
from libs.security import hash_password
from libs.email_generator import generate_unique_company_email
from setting import settings


async def seed_superadmin():
    fullname = settings.SUPER_ADMIN_NAME
    personal_email = settings.SUPER_ADMIN_EMAIL
    raw_password = settings.SUPER_ADMIN_PASSWORD
    phone = settings.SUPER_ADMIN_PHONE

    async with LocalSession() as db:
        existing = await db.scalar(
            select(Admin).where(
                (Admin.personal_email == personal_email) | (Admin.role == AdminRole.SUPER_ADMIN)
            )
        )
        if existing:
            print(f"Superadmin already exists: {existing.company_email} / {existing.personal_email}")
            return

        company_email = await generate_unique_company_email(db, fullname)
        hashed = hash_password(raw_password)

        superadmin = Admin(
            fullname=fullname,
            company_email=company_email,
            personal_email=personal_email,
            phone=phone,
            password=hashed,
            role=AdminRole.SUPER_ADMIN,
            permission=[AdminPermission.MANAGE_ALL],
            status=AdminStatus.ACTIVE,
        )

        db.add(superadmin)
        await db.commit()
        await db.refresh(superadmin)

        print(f"Superadmin created successfully!")
        print(f"Company Email: {superadmin.company_email}")
        print(f"Personal Email: {superadmin.personal_email}")
        print(f"Password: {raw_password}")


if __name__ == "__main__":
    asyncio.run(seed_superadmin())
