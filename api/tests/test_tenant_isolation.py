import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_staff_cannot_access_other_store_products(client: AsyncClient, seed_data: dict):
    headers_1 = {"Authorization": f"Bearer {seed_data['token_1']}"}
    store_2_id = seed_data["store_2"].store_id

    res = await client.get(f"/api/v1/{store_2_id}/product/", headers=headers_1)
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_staff_can_access_own_store_products(client: AsyncClient, seed_data: dict):
    headers_1 = {"Authorization": f"Bearer {seed_data['token_1']}"}
    store_1_id = seed_data["store_1"].store_id
    slug_1 = seed_data["product_1"].slug

    res = await client.get(f"/api/v1/{store_1_id}/product/", headers=headers_1)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["slug"] == slug_1


@pytest.mark.asyncio
async def test_staff_cannot_delete_other_store_product(client: AsyncClient, seed_data: dict):
    headers_2 = {"Authorization": f"Bearer {seed_data['token_2']}"}
    store_2_id = seed_data["store_2"].store_id
    slug_1 = seed_data["product_1"].slug

    res = await client.delete(f"/api/v1/{store_2_id}/product/{slug_1}", headers=headers_2)
    assert res.status_code == 404
