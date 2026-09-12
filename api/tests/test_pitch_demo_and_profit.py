import pytest
import uuid
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient
from sqlalchemy import select
from models.user import User, StoreMember, UserSession
from models.business import Store
from models.stock import Stock, Sale, SaleItem
from models.subscription import UserSubscription
from models.admin.plan import Plan
from schemas.user import StaffPermission, StaffStatus, UserStatus
from schemas.business import StoreStatus
from schemas.subscription import PlanStatus
from libs.security import hash_password, create_access_token, hash_token
from setting import settings


@pytest.mark.asyncio
async def test_sale_item_cost_price_snapshot_and_permission_masking(client: AsyncClient, seed_data: dict, db_session):
    store_1 = seed_data["store_1"]
    owner = seed_data["owner"]

    # Create valid session and token for store owner
    owner_session = UserSession(
        session_id=uuid.uuid4(),
        user_id=owner.user_id,
        refresh_token_hash=hash_token(f"owner_ref_{uuid.uuid4().hex[:6]}"),
        expired_at=datetime.now(timezone.utc) + timedelta(days=7),
        created_at=datetime.now(timezone.utc),
        ip_address="127.0.0.1",
        user_agent="pytest"
    )
    db_session.add(owner_session)
    await db_session.flush()

    token_owner = create_access_token({"sub": str(owner.user_id), "session_id": str(owner_session.session_id)})
    headers_owner = {"Authorization": f"Bearer {token_owner}"}

    # Grant VIEW_SALES to cashier member_1 so they have [RECORD_SALES, VIEW_PRODUCT, VIEW_SALES] but NOT VIEW_PROFIT
    member_1 = seed_data["member_1"]
    member_1.permission = [
        StaffPermission.RECORD_SALES.value,
        StaffPermission.VIEW_PRODUCT.value,
        StaffPermission.VIEW_SALES.value,
    ]
    await db_session.commit()

    token_cashier = seed_data["token_1"]
    headers_cashier = {"Authorization": f"Bearer {token_cashier}"}

    # 1. Create a product with cost_price = 15000 (₦150) and unit_price = 25000 (₦250)
    uid = uuid.uuid4().hex[:6]
    product_slug = f"cost-test-{uid}"
    prod = Stock(
        name="Cost Test Item",
        slug=product_slug,
        unit_price=25000,
        cost_price=15000,
        quantities=10.0,
        unit_in="piece",
        store_id=store_1.store_id,
        deleted=False
    )
    db_session.add(prod)
    await db_session.commit()

    # 2. Check GET /products as cashier: cost_price should be MASKED (None)
    res_cashier_prod = await client.get(f"/api/v1/{store_1.store_id}/product", headers=headers_cashier)
    assert res_cashier_prod.status_code == 200
    cashier_prods = res_cashier_prod.json()
    item_cashier = next(p for p in cashier_prods if p["slug"] == product_slug)
    assert item_cashier["cost_price"] is None

    # Check GET /products as owner: cost_price is 15000
    res_owner_prod = await client.get(f"/api/v1/{store_1.store_id}/product", headers=headers_owner)
    assert res_owner_prod.status_code == 200
    owner_prods = res_owner_prod.json()
    item_owner = next(p for p in owner_prods if p["slug"] == product_slug)
    assert item_owner["cost_price"] == 15000

    # 3. Cashier records a sale: 2 quantities at 25000 each (total 50000)
    idempotency_key = str(uuid.uuid4())
    payload = [
        {
            "idempotency_key": idempotency_key,
            "items": [
                {
                    "stock_slug": product_slug,
                    "quantities": 2,
                    "amount": 25000
                }
            ],
            "discount": 5000,
            "payment_method": "cash",
            "amount_recived": 45000,
            "status": "completed"
        }
    ]

    res_sale = await client.post(f"/api/v1/{store_1.store_id}/sales/", json=payload, headers=headers_cashier)
    assert res_sale.status_code == 201

    # 4. Verify in DB that SaleItem has snapshotted cost_price = 15000
    sale_db = (await db_session.execute(select(Sale).where(Sale.idempotency_key == uuid.UUID(idempotency_key)))).scalar_one()
    sale_item_db = (await db_session.execute(select(SaleItem).where(SaleItem.sale_id == sale_db.sale_id))).scalar_one()
    assert sale_item_db.cost_price == 15000

    # 5. Check GET /sales as cashier: cost_price should be masked to None
    res_sales_cashier = await client.get(f"/api/v1/{store_1.store_id}/sales", headers=headers_cashier)
    assert res_sales_cashier.status_code == 200
    sales_data_cashier = res_sales_cashier.json()["items"]
    target_sale_c = next(s for s in sales_data_cashier if s["sale_id"] == str(sale_db.sale_id))
    assert target_sale_c["items"][0]["cost_price"] is None

    # Check GET /sales as owner: cost_price is 15000
    res_sales_owner = await client.get(f"/api/v1/{store_1.store_id}/sales", headers=headers_owner)
    assert res_sales_owner.status_code == 200
    sales_data_owner = res_sales_owner.json()["items"]
    target_sale_o = next(s for s in sales_data_owner if s["sale_id"] == str(sale_db.sale_id))
    assert target_sale_o["items"][0]["cost_price"] == 15000


@pytest.mark.asyncio
async def test_demo_reset_data_security_and_wipe(client: AsyncClient, seed_data: dict, db_session):
    store_1 = seed_data["store_1"]
    token_1 = seed_data["token_1"]
    headers_1 = {"Authorization": f"Bearer {token_1}"}

    # 1. Attempt reset with a regular non-demo user -> MUST return 403
    res_forbidden = await client.post(
        f"/api/v1/store/{store_1.store_id}/reset-demo-data",
        json={"wipe_mode": "sales_only"},
        headers=headers_1
    )
    assert res_forbidden.status_code == 403
    assert "not in the demo allowlist" in res_forbidden.json()["detail"]

    # 2. Create an authorized demo store owner
    demo_email = "demo@kluda.com"
    demo_owner = User(
        user_id=uuid.uuid4(),
        fullname="Demo Pitcher",
        email=demo_email,
        password=hash_password("DemoPass123!"),
        status=UserStatus.ACTIVE
    )
    db_session.add(demo_owner)
    await db_session.flush()

    demo_store = Store(
        store_id=uuid.uuid4(),
        name="Demo Pitch Store",
        category="Pitch Demo",
        address="Pitch Venue",
        status=StoreStatus.ACTIVE,
        user_id=demo_owner.user_id
    )
    db_session.add(demo_store)
    await db_session.flush()

    demo_member = StoreMember(
        store_id=demo_store.store_id,
        user_id=demo_owner.user_id,
        role="owner",
        permission=["manage:all"],
        status=StaffStatus.ACTIVE
    )
    db_session.add(demo_member)

    # Add user session for demo owner
    demo_session = UserSession(
        session_id=uuid.uuid4(),
        user_id=demo_owner.user_id,
        refresh_token_hash=hash_token(f"demo_ref_{uuid.uuid4().hex[:6]}"),
        expired_at=datetime.now(timezone.utc) + timedelta(days=7),
        created_at=datetime.now(timezone.utc),
        ip_address="127.0.0.1",
        user_agent="pytest"
    )
    db_session.add(demo_session)
    await db_session.flush()

    # Add a product and a sale to demo store
    demo_prod = Stock(
        name="Pitch Cola",
        slug=f"pitch-cola-{uuid.uuid4().hex[:4]}",
        unit_price=50000,
        cost_price=30000,
        quantities=20.0,
        unit_in="piece",
        store_id=demo_store.store_id,
        deleted=False
    )
    db_session.add(demo_prod)
    await db_session.flush()

    demo_sale = Sale(
        sale_id=uuid.uuid4(),
        store_id=demo_store.store_id,
        user_id=demo_owner.user_id,
        idempotency_key=uuid.uuid4(),
        payment_method="cash",
        amount_recived=50000,
        discount=0,
        status="completed"
    )
    db_session.add(demo_sale)
    await db_session.flush()

    demo_item = SaleItem(
        sale_id=demo_sale.sale_id,
        stock_slug=demo_prod.slug,
        amount=50000,
        quantities=1.0,
        cost_price=30000
    )
    db_session.add(demo_item)
    await db_session.commit()

    demo_token = create_access_token({"sub": str(demo_owner.user_id), "session_id": str(demo_session.session_id)})
    headers_demo = {"Authorization": f"Bearer {demo_token}"}

    # 3. Test sales_only reset: wipes sales but keeps product for next pitch
    res_reset_sales = await client.post(
        f"/api/v1/store/{demo_store.store_id}/reset-demo-data",
        json={"wipe_mode": "sales_only"},
        headers=headers_demo
    )
    assert res_reset_sales.status_code == 200
    data_reset = res_reset_sales.json()
    assert data_reset["success"] is True
    assert data_reset["deleted_counts"]["sales"] == 1
    assert data_reset["deleted_counts"]["products"] == 0

    # Verify product still exists in DB
    p_check = await db_session.scalar(select(Stock).where(Stock.store_id == demo_store.store_id))
    assert p_check is not None

    # Verify sales are 0
    s_check = await db_session.scalar(select(Sale).where(Sale.store_id == demo_store.store_id))
    assert s_check is None

    # 4. Test full_wipe reset: also wipes products
    res_full_wipe = await client.post(
        f"/api/v1/store/{demo_store.store_id}/reset-demo-data",
        json={"wipe_mode": "full_wipe"},
        headers=headers_demo
    )
    assert res_full_wipe.status_code == 200
    data_full = res_full_wipe.json()
    assert data_full["success"] is True
    assert data_full["deleted_counts"]["products"] == 1

    # Product should now be deleted
    p_check_2 = await db_session.scalar(select(Stock).where(Stock.store_id == demo_store.store_id))
    assert p_check_2 is None


@pytest.mark.asyncio
async def test_dynamic_default_plan_assignment_on_register(client: AsyncClient, db_session):
    # 1. Create a default early access plan (price = 0, is_default = True)
    slug = f"early-access-{uuid.uuid4().hex[:6]}"
    early_plan = Plan(
        slug=slug,
        name=f"Early Access {slug}",
        description="Free Early Access for Pitching",
        price=0,
        interval="monthly",
        has_trial=False,
        is_default=True,
        status=PlanStatus.AVAILABLE,
        store_limit=3,
        product_limit=500,
        sales_limit_per_month=1000,
        analytics_read_per_month=200
    )
    db_session.add(early_plan)
    await db_session.commit()

    # 2. Register a new user
    user_email = f"new_pitch_{uuid.uuid4().hex[:6]}@example.com"
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "fullname": "New Pitch User",
            "email": user_email,
            "password": "Password123!",
            "phone": "+2348011223344",
            "store_name": "New Pitch Branch"
        }
    )
    assert reg_res.status_code == 201

    # 3. Verify user's subscription was assigned to the default early access plan
    user_db = await db_session.scalar(select(User).where(User.email == user_email))
    assert user_db is not None
    user_sub = await db_session.scalar(select(UserSubscription).where(UserSubscription.user_id == user_db.user_id))
    assert user_sub is not None
    assert user_sub.plan_id == slug
