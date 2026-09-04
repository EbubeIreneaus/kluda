import pytest
import uuid
from datetime import datetime, timezone, timedelta
from models.store_audit import StoreAuditLog
from models.user import UserSession
from libs.audit import record_store_audit
from libs.security import create_access_token, hash_token


@pytest.mark.asyncio
async def test_record_store_audit_helper(db_session, seed_data):
    store = seed_data["store_1"]
    owner = seed_data["owner"]

    log = await record_store_audit(
        db=db_session,
        store_id=store.store_id,
        action="product.create",
        target_type="product",
        actor=owner,
        target_id="test-slug-1",
        target_name="Test Product",
        details={"price": 1000},
        ip_address="127.0.0.1",
    )
    await db_session.commit()

    assert log.id is not None
    assert log.store_id == store.store_id
    assert log.actor_id == owner.user_id
    assert log.actor_name == owner.fullname
    assert log.action == "product.create"
    assert log.target_type == "product"
    assert log.target_id == "test-slug-1"
    assert log.target_name == "Test Product"
    assert log.details == {"price": 1000}
    assert log.ip_address == "127.0.0.1"


@pytest.mark.asyncio
async def test_audit_log_endpoint_owner_access(client, db_session, seed_data):
    store = seed_data["store_1"]
    owner = seed_data["owner"]

    session = UserSession(
        session_id=uuid.uuid4(),
        user_id=owner.user_id,
        refresh_token_hash=hash_token("owner_ref_1"),
        expired_at=datetime.now(timezone.utc) + timedelta(days=7),
        created_at=datetime.now(timezone.utc),
        ip_address="127.0.0.1",
        user_agent="pytest",
    )
    db_session.add(session)
    await db_session.flush()
    owner_token = create_access_token({"sub": str(owner.user_id), "session_id": str(session.session_id)})

    await record_store_audit(
        db=db_session,
        store_id=store.store_id,
        action="product.create",
        target_type="product",
        actor=owner,
        target_id="prod-1",
        target_name="Product 1",
    )
    await record_store_audit(
        db=db_session,
        store_id=store.store_id,
        action="customer.delete",
        target_type="customer",
        actor=owner,
        target_id="cust-1",
        target_name="Customer 1",
    )
    await db_session.commit()

    response = await client.get(
        f"/api/v1/{store.store_id}/audit-logs",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["items"][0]["action"] == "customer.delete"
    assert data["items"][1]["action"] == "product.create"


@pytest.mark.asyncio
async def test_audit_log_endpoint_filtering(client, db_session, seed_data):
    store = seed_data["store_1"]
    owner = seed_data["owner"]

    session = UserSession(
        session_id=uuid.uuid4(),
        user_id=owner.user_id,
        refresh_token_hash=hash_token("owner_ref_2"),
        expired_at=datetime.now(timezone.utc) + timedelta(days=7),
        created_at=datetime.now(timezone.utc),
        ip_address="127.0.0.1",
        user_agent="pytest",
    )
    db_session.add(session)
    await db_session.flush()
    owner_token = create_access_token({"sub": str(owner.user_id), "session_id": str(session.session_id)})

    await record_store_audit(
        db=db_session,
        store_id=store.store_id,
        action="product.create",
        target_type="product",
        actor=owner,
        target_id="prod-1",
        target_name="Basmati Rice",
    )
    await record_store_audit(
        db=db_session,
        store_id=store.store_id,
        action="customer.create",
        target_type="customer",
        actor=owner,
        target_id="cust-1",
        target_name="Alice Wonder",
    )
    await db_session.commit()

    res_action = await client.get(
        f"/api/v1/{store.store_id}/audit-logs?action=product.create",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res_action.status_code == 200
    assert res_action.json()["total"] == 1
    assert res_action.json()["items"][0]["target_name"] == "Basmati Rice"

    res_type = await client.get(
        f"/api/v1/{store.store_id}/audit-logs?target_type=customer",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res_type.status_code == 200
    assert res_type.json()["total"] == 1
    assert res_type.json()["items"][0]["target_name"] == "Alice Wonder"

    res_search = await client.get(
        f"/api/v1/{store.store_id}/audit-logs?search=Basmati",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res_search.status_code == 200
    assert res_search.json()["total"] == 1
    assert res_search.json()["items"][0]["target_name"] == "Basmati Rice"


@pytest.mark.asyncio
async def test_audit_log_endpoint_permission_denied_for_regular_staff(client, seed_data):
    store = seed_data["store_1"]
    token_1 = seed_data["token_1"]

    response = await client.get(
        f"/api/v1/{store.store_id}/audit-logs",
        headers={"Authorization": f"Bearer {token_1}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_audit_log_endpoint_allowed_for_manager_with_manage_all(client, seed_data):
    store = seed_data["store_2"]
    token_2 = seed_data["token_2"]

    response = await client.get(
        f"/api/v1/{store.store_id}/audit-logs",
        headers={"Authorization": f"Bearer {token_2}"},
    )
    assert response.status_code == 200
