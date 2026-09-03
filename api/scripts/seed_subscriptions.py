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
                "name": "Free Starter Tier",
                "description": "Essential single-store retail operations with offline checkout.",
                "price": 0,
                "interval": "monthly",
                "has_trial": False,
                "trial_duration_days": 0,
                "store_limit": 1,
                "product_limit": 100,
                "sales_limit_per_month": 500,
                "analytics_read_per_month": 50,
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
                existing.has_trial = p_data["has_trial"]
                existing.trial_duration_days = p_data["trial_duration_days"]
                existing.interval = p_data["interval"]
                print(f"Plan updated: {existing.name} ({existing.slug}) - Trial: {existing.has_trial}")

        # Ensure standalone trial plan is deactivated
        old_trial = await db.scalar(select(Plan).where(Plan.slug == "trial"))
        if old_trial:
            old_trial.status = PlanStatus.UNAVAILABLE
            print("Deactivated legacy standalone trial plan.")

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
