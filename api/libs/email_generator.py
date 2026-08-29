import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.admin.user import Admin
from setting import settings


async def generate_unique_company_email(db: AsyncSession, fullname: str) -> str:
    cleaned = re.sub(r'[^a-zA-Z\s]', '', fullname).strip().lower()
    parts = cleaned.split()
    first = parts[0] if len(parts) > 0 else "admin"
    last = parts[-1] if len(parts) > 1 else ""

    domain = settings.DOMAIN_NAME if hasattr(settings, "DOMAIN_NAME") and settings.DOMAIN_NAME else "kluda.app"
    if domain.startswith("http://") or domain.startswith("https://"):
        domain = domain.split("://")[-1]
    domain = domain.split(":")[0]

    candidate = f"{first}@{domain}"
    existing = await db.scalar(select(Admin).where(Admin.company_email == candidate))
    if not existing:
        return candidate

    if last:
        candidate = f"{first}.{last[0]}@{domain}"
        existing = await db.scalar(select(Admin).where(Admin.company_email == candidate))
        if not existing:
            return candidate

        candidate = f"{first}.{last}@{domain}"
        existing = await db.scalar(select(Admin).where(Admin.company_email == candidate))
        if not existing:
            return candidate

    counter = 1
    while True:
        candidate = f"{first}{counter}@{domain}" if not last else f"{first}.{last}{counter}@{domain}"
        existing = await db.scalar(select(Admin).where(Admin.company_email == candidate))
        if not existing:
            return candidate
        counter += 1
