import pytest
import uuid
from models.catalog import CatalogTemplate, CatalogItem
from models.stock import Stock
from libs.cache import delete_cache_pattern
from sqlalchemy import select


@pytest.mark.asyncio
async def test_catalog_templates_and_import(client, db_session, seed_data):
    # Ensure fresh cache state
    await delete_cache_pattern("catalog:*")

    # 1. Create a sample template with items in test db
    template = CatalogTemplate(
        name="Supermarket Express",
        slug="supermarket-express",
        description="Quick starter pack",
        icon=None,  # test null icon fallback
        is_active=True,
        sort_order=1,
    )
    db_session.add(template)
    await db_session.flush()
    await db_session.refresh(template)

    item_1 = CatalogItem(
        template_id=template.id,
        name="Golden Penny Pasta 500g",
        barcode="123456789012",
        category="Pasta",
        suggested_price=35000,
        cost_price=28000,
        unit_in="piece",
        description="Tasty pasta",
        is_active=True,
    )
    item_2 = CatalogItem(
        template_id=template.id,
        name="Peak Milk 400g",  # Same name as product_2 in seed_data for store_2
        barcode="999888777666",
        category="Dairy",
        suggested_price=180000,
        cost_price=150000,
        unit_in="piece",
        is_active=True,
    )
    item_3 = CatalogItem(
        template_id=template.id,
        name="Dano Milk 400g",
        barcode=seed_data["product_2"].barcode_id,  # Same barcode as product_2 in store_2
        category="Dairy",
        suggested_price=170000,
        cost_price=140000,
        unit_in="piece",
        is_active=True,
    )
    item_4 = CatalogItem(
        template_id=template.id,
        name="Milo Refill 500g",
        barcode="555666777888",
        category="Beverages",
        suggested_price=250000,
        cost_price=210000,
        unit_in="piece",
        is_active=True,
    )
    db_session.add_all([item_1, item_2, item_3, item_4])
    await db_session.commit()

    # 2. Test GET /api/v1/catalog-templates
    res = await client.get("/api/v1/catalog-templates")
    assert res.status_code == 200
    templates_list = res.json()
    assert len(templates_list) >= 1
    target = next((t for t in templates_list if t["slug"] == "supermarket-express"), None)
    assert target is not None
    assert target["total_items"] == 4
    # Ensure default icon was provided even when db has None
    assert target["icon"] == "package"

    # 3. Test GET /api/v1/catalog-templates/{slug}
    res = await client.get("/api/v1/catalog-templates/supermarket-express")
    assert res.status_code == 200
    tmpl_data = res.json()
    assert tmpl_data["name"] == "Supermarket Express"
    assert tmpl_data["icon"] == "package"
    assert tmpl_data["total_items"] == 4

    # 4. Test GET /api/v1/catalog-templates/{slug}/items
    res = await client.get("/api/v1/catalog-templates/supermarket-express/items?page=1&page_size=10")
    assert res.status_code == 200
    items_data = res.json()
    assert items_data["total"] == 4
    assert len(items_data["items"]) == 4

    # 5. Test POST /api/v1/catalog-templates/{slug}/import
    store_2_id = str(seed_data["store_2"].store_id)
    headers = {"Authorization": f"Bearer {seed_data['token_2']}"}

    import_res = await client.post(
        f"/api/v1/catalog-templates/supermarket-express/import?store_id={store_2_id}",
        headers=headers,
    )
    assert import_res.status_code == 200
    import_data = import_res.json()

    # item_1 (Golden Penny) and item_4 (Milo Refill) should be imported.
    # item_2 has same name as product_2 ("Peak Milk 400g") -> skipped.
    # item_3 has same barcode as product_2 -> skipped.
    assert import_data["imported"] == 2
    assert import_data["skipped"] == 2

    # Verify products exist in stock with correct cost_price and suggested price
    pasta = await db_session.scalar(
        select(Stock).where(
            Stock.store_id == seed_data["store_2"].store_id,
            Stock.barcode_id == "123456789012",
        )
    )
    assert pasta is not None
    assert pasta.name == "Golden Penny Pasta 500g"
    assert pasta.unit_price == 35000
    assert pasta.cost_price == 28000
    assert pasta.quantities == 0
    assert pasta.unit_in == "piece"

    # 6. Test idempotent import (running again should skip all)
    re_import_res = await client.post(
        f"/api/v1/catalog-templates/supermarket-express/import?store_id={store_2_id}",
        headers=headers,
    )
    assert re_import_res.status_code == 200
    re_data = re_import_res.json()
    assert re_data["imported"] == 0
    assert re_data["skipped"] == 4

    # 7. Check that total_imports metric on template was incremented
    await db_session.refresh(template)
    assert template.total_imports >= 1
