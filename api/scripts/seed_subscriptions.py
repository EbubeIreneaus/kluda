import asyncio
import os
import sys
from datetime import datetime, timezone, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select
from models.config import LocalSession
from models.admin.plan import Plan
from models.user import User
from models.business import Store
from models.subscription import UserSubscription
from schemas.subscription import PlanStatus, SubscriptionStatus, PaymentChannel


async def seed_subscriptions():
    async with LocalSession() as db:
        default_plans = [
            {
                "slug": "free",
                "name": "Free Tier",
                "description": "Essential single-store retail operations with offline checkout.",
                "price": 0,
                "store_limit": 1,
                "product_limit": 100,
                "sales_limit_per_month": 200,
                "analytics_read_per_month": 50,
                "status": PlanStatus.AVAILABLE,
                "paystack_planid": None,
            },
            {
                "slug": "trial",
                "name": "30-Day Pro Trial",
                "description": "Full-access 30-day trial with multi-branch synchronization and advanced reports.",
                "price": 0,
                "store_limit": 3,
                "product_limit": 1000,
                "sales_limit_per_month": 5000,
                "analytics_read_per_month": 500,
                "status": PlanStatus.AVAILABLE,
                "paystack_planid": None,
            }
        ]

        for p_data in default_plans:
            existing = await db.scalar(select(Plan).where(Plan.slug == p_data["slug"]))
            if not existing:
                plan = Plan(**p_data)
                db.add(plan)
                print(f"Created plan: {p_data['name']} ({p_data['slug']})")
            else:
                print(f"Plan already exists: {existing.name} ({existing.slug})")

        await db.flush()

        stores = (await db.scalars(select(Store))).all()
        unique_owners: dict[str, User] = {}

        for store in stores:
            if store.user_id and str(store.user_id) not in unique_owners:
                owner = await db.scalar(select(User).where(User.user_id == store.user_id))
                if owner:
                    unique_owners[str(owner.user_id)] = owner

        all_users = (await db.scalars(select(User))).all()
        for u in all_users:
            if str(u.user_id) not in unique_owners:
                unique_owners[str(u.user_id)] = u

        created_subs_count = 0
        now = datetime.now(timezone.utc)
        for owner in unique_owners.values():
            if owner.current_subscription_id is None:
                free_sub = UserSubscription(
                    user_id=owner.user_id,
                    plan_id="free",
                    status=SubscriptionStatus.ACTIVE,
                    amount=0,
                    payment_channel=PaymentChannel.PAYSTACK,
                    next_renewal=now + timedelta(days=36500),
                    idempotency_key=f"seed_free_{owner.user_id}",
                )
                db.add(free_sub)
                await db.flush()
                owner.current_subscription_id = free_sub.subscription_id
                created_subs_count += 1
                print(f"Assigned Free Tier to user: {owner.fullname} ({owner.email})")

        await db.commit()
        print(f"Subscription seed complete! {created_subs_count} users assigned to Free Tier.")


if __name__ == "__main__":
    asyncio.run(seed_subscriptions())
