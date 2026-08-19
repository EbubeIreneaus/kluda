import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy import select
from models.stock import Stock, StockHistory


@pytest.mark.asyncio
async def test_stock_history_increments_and_decrements(client: AsyncClient, seed_data: dict, db_session):
    headers_2 = {"Authorization": f"Bearer {seed_data['token_2']}"}
    store_2_id = seed_data["store_2"].store_id
    slug_2 = seed_data["product_2"].slug

    payload_add = {
        "stock_slug": slug_2,
        "quantity": 5.0,
        "action_type": "addition",
        "reason": "restock",
        "note": "Shipment #101"
    }
    res_add = await client.post(f"/api/v1/{store_2_id}/product/stock-history", json=payload_add, headers=headers_2)
    assert res_add.status_code == 201
    data_add = res_add.json()
    assert data_add["stock_slug"] == slug_2
    assert float(data_add["quantity"]) == 5.0

    stk_res = await db_session.execute(select(Stock).where(Stock.slug == slug_2))
    product = stk_res.scalar_one_or_none()
    assert product is not None
    assert float(product.quantities) == 25.0

    payload_sub = {
        "stock_slug": slug_2,
        "quantity": 3.0,
        "action_type": "subtract",
        "reason": "damage",
        "note": "Broken seal"
    }
    res_sub = await client.post(f"/api/v1/{store_2_id}/product/stock-history", json=payload_sub, headers=headers_2)
    assert res_sub.status_code == 201

    await db_session.refresh(product)
    assert float(product.quantities) == 22.0

    res_history = await client.get(f"/api/v1/{store_2_id}/product/stock-history?slug={slug_2}", headers=headers_2)
    assert res_history.status_code == 200
    histories = res_history.json()
    assert len(histories) == 2


@pytest.mark.asyncio
async def test_product_update_ignores_quantity_override(client: AsyncClient, seed_data: dict, db_session):
    headers_2 = {"Authorization": f"Bearer {seed_data['token_2']}"}
    store_2_id = seed_data["store_2"].store_id
    slug_2 = seed_data["product_2"].slug

    update_payload = {
        "name": "Peak Milk 400g Premium",
        "quantities": 999.0
    }
    res = await client.put(f"/api/v1/{store_2_id}/product/{slug_2}", json=update_payload, headers=headers_2)
    assert res.status_code == 200

    stk_res = await db_session.execute(select(Stock).where(Stock.slug == slug_2))
    product = stk_res.scalar_one_or_none()
    assert product is not None
    assert product.name == "Peak Milk 400g Premium"
    assert float(product.quantities) != 999.0


@pytest.mark.asyncio
async def test_sso_ticket_lifecycle_and_exchange(client: AsyncClient, seed_data: dict):
    headers_2 = {"Authorization": f"Bearer {seed_data['token_2']}"}

    res_tkt = await client.post("/api/v1/auth/sso/ticket", headers=headers_2)
    assert res_tkt.status_code == 200
    tkt_data = res_tkt.json()
    assert "ticket" in tkt_data
    assert tkt_data["ticket"].startswith("sso_")

    ticket = tkt_data["ticket"]
    res_exchange = await client.post("/api/v1/auth/sso/exchange", json={"ticket": ticket})
    assert res_exchange.status_code == 200
    exch_data = res_exchange.json()
    assert exch_data["success"] is True
    assert "access_token" in exch_data
    assert len(exch_data["stores"]) >= 1

    res_reuse = await client.post("/api/v1/auth/sso/exchange", json={"ticket": ticket})
    assert res_reuse.status_code == 400


@pytest.mark.asyncio
async def test_universal_login_with_owner_email(client: AsyncClient, seed_data: dict):
    owner = seed_data["owner"]
    login_payload = {
        "staff_id": owner.email,
        "password": "password123"
    }
    res = await client.post("/api/v1/staff/auth/login", json=login_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["staff"]["role"] == "owner"
    assert len(data["stores"]) >= 1
