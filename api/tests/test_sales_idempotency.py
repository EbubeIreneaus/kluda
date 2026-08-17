import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy import select
from models.stock import Stock, Sale


@pytest.mark.asyncio
async def test_bulk_sale_creation_and_idempotency(client: AsyncClient, seed_data: dict, db_session):
    headers_1 = {"Authorization": f"Bearer {seed_data['token_1']}"}
    store_1_id = seed_data["store_1"].store_id
    slug_1 = seed_data["product_1"].slug
    idempotency_key = str(uuid.uuid4())

    payload = [
        {
            "idempotency_key": idempotency_key,
            "items": [
                {
                    "stock_slug": slug_1,
                    "quantities": 2,
                    "amount": 250000
                }
            ],
            "discount": 0,
            "payment_method": "cash",
            "amount_recived": 500000,
            "status": "completed",
            "staff_note": "Test sale"
        }
    ]

    res1 = await client.post(f"/api/v1/{store_1_id}/sales/", json=payload, headers=headers_1)
    assert res1.status_code == 201
    data1 = res1.json()
    assert data1["success"] is True
    assert data1["created_count"] == 1
    assert idempotency_key in data1["synced_keys"]

    stk_res = await db_session.execute(select(Stock).where(Stock.slug == slug_1))
    stock = stk_res.scalar_one_or_none()
    assert stock is not None
    assert float(stock.quantities) == 8.0

    res2 = await client.post(f"/api/v1/{store_1_id}/sales/", json=payload, headers=headers_1)
    assert res2.status_code == 201
    data2 = res2.json()
    assert data2["success"] is True
    assert data2["created_count"] == 0
    assert idempotency_key in data2["synced_keys"]

    stk_res_2 = await db_session.execute(select(Stock).where(Stock.slug == slug_1))
    stock_2 = stk_res_2.scalar_one_or_none()
    assert stock_2 is not None
    assert float(stock_2.quantities) == 8.0

    sales_res = await db_session.execute(select(Sale).where(Sale.idempotency_key == uuid.UUID(idempotency_key)))
    sales = sales_res.scalars().all()
    assert len(sales) == 1
