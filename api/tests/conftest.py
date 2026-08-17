import pytest
import pytest_asyncio
import uuid
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from models.config import Base, get_db
from models.user import User, Staff, UserSession, StaffSession, Customer
from models.business import Store
from models.stock import Stock, Sale, SaleItem
from libs.security import hash_password, create_access_token, hash_token
from schemas.user import StaffPermission, StaffStatus, UserStatus
from schemas.business import StoreStatus
from main import app

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)


@pytest_asyncio.fixture(autouse=True)
async def prepare_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session():
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def seed_data(db_session: AsyncSession):
    uid = uuid.uuid4().hex[:6]
    owner = User(
        user_id=uuid.uuid4(),
        fullname="Test Owner",
        email=f"owner_{uid}@test.com",
        password=hash_password("password123"),
        status=UserStatus.ACTIVE
    )
    db_session.add(owner)
    await db_session.flush()

    store_1 = Store(
        store_id=uuid.uuid4(),
        name=f"Store Alpha {uid}",
        category="General Retail",
        address="10 Alpha Street",
        status=StoreStatus.ACTIVE,
        user_id=owner.user_id
    )
    store_2 = Store(
        store_id=uuid.uuid4(),
        name=f"Store Beta {uid}",
        category="Supermarket",
        address="20 Beta Avenue",
        status=StoreStatus.ACTIVE,
        user_id=owner.user_id
    )
    db_session.add_all([store_1, store_2])
    await db_session.flush()

    staff_1 = Staff(
        staff_id=f"STF{uid[:3]}1",
        first_name="Alice",
        last_name="Cashier",
        role="cashier",
        email=f"alice_{uid}@alpha.com",
        password=hash_password("staffpass1"),
        permission=[StaffPermission.RECORD_SALES.value, StaffPermission.VIEW_PRODUCT.value],
        status=StaffStatus.ACTIVE,
        store_id=store_1.store_id
    )
    staff_2 = Staff(
        staff_id=f"STF{uid[:3]}2",
        first_name="Bob",
        last_name="Manager",
        role="manager",
        email=f"bob_{uid}@beta.com",
        password=hash_password("staffpass2"),
        permission=[StaffPermission.RECORD_SALES.value, StaffPermission.MANAGE_PRODUCT.value, StaffPermission.MANAGE_STAFF.value],
        status=StaffStatus.ACTIVE,
        store_id=store_2.store_id
    )
    db_session.add_all([staff_1, staff_2])
    await db_session.flush()

    session_1 = StaffSession(
        session_id=uuid.uuid4(),
        staff_id=staff_1.staff_id,
        refresh_token_hash=hash_token(f"mock_ref_1_{uid}"),
        expired_at=datetime.now(timezone.utc) + timedelta(days=7),
        created_at=datetime.now(timezone.utc),
        ip_address="127.0.0.1",
        user_agent="pytest"
    )
    session_2 = StaffSession(
        session_id=uuid.uuid4(),
        staff_id=staff_2.staff_id,
        refresh_token_hash=hash_token(f"mock_ref_2_{uid}"),
        expired_at=datetime.now(timezone.utc) + timedelta(days=7),
        created_at=datetime.now(timezone.utc),
        ip_address="127.0.0.1",
        user_agent="pytest"
    )
    db_session.add_all([session_1, session_2])
    await db_session.flush()

    token_1 = create_access_token({"sub": staff_1.staff_id, "session_id": str(session_1.session_id)})
    token_2 = create_access_token({"sub": staff_2.staff_id, "session_id": str(session_2.session_id)})
    staff_1.access_token = token_1
    staff_2.access_token = token_2

    product_1 = Stock(
        name="Milo 500g",
        slug=f"milo-500g-alpha-{uid}",
        unit_price=250000,
        quantities=10,
        unit_in="piece",
        barcode_id=f"111222{uid}",
        store_id=store_1.store_id
    )
    product_2 = Stock(
        name="Peak Milk 400g",
        slug=f"peak-milk-beta-{uid}",
        unit_price=180000,
        quantities=20,
        unit_in="piece",
        barcode_id=f"444555{uid}",
        store_id=store_2.store_id
    )
    db_session.add_all([product_1, product_2])
    await db_session.commit()

    return {
        "owner": owner,
        "store_1": store_1,
        "store_2": store_2,
        "staff_1": staff_1,
        "staff_2": staff_2,
        "session_1": session_1,
        "session_2": session_2,
        "token_1": token_1,
        "token_2": token_2,
        "product_1": product_1,
        "product_2": product_2
    }
