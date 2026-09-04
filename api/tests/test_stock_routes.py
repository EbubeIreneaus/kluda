import pytest
import uuid
from schemas.stock import (
    StockCreate,
    StockResponse,
    SaleCreate,
    SaleItemCreate,
    SaleResponse,
    BarcodeResponse,
)
from schemas.user import CustomerResponse, DebtResponse


def test_no_id_in_response_schemas():
    for schema_cls in [
        StockResponse,
        SaleResponse,
        CustomerResponse,
        DebtResponse,
        BarcodeResponse,
    ]:
        fields = schema_cls.model_fields
        assert "id" not in fields, f"Schema {schema_cls.__name__} must not contain 'id' field"


def test_stock_create_schema():
    stock = StockCreate(
        name="Basmati Rice 5kg",
        unit_price=1500000,
        sku="RIC-001",
        quantities=10.0,
        unit_in="pack",
    )
    assert stock.name == "Basmati Rice 5kg"
    assert stock.unit_price == 1500000
    assert stock.unit_in == "pack"


def test_sale_create_schema():
    customer_id = uuid.uuid4()
    sale = SaleCreate(
        idempotency_key=uuid.uuid4(),
        items=[
            SaleItemCreate(stock_slug="basmati-rice-5kg", amount=1500000, quantities=2.0)
        ],
        discount=50000,
        customer_id=customer_id,
        payment_method="cash",
        amount_recived=3000000,
    )
    assert len(sale.items) == 1
    assert sale.payment_method == "cash"
    assert sale.customer_id == customer_id


@pytest.mark.asyncio
async def test_same_barcode_across_different_stores(db_session, seed_data):
    from models.stock import Stock
    shared_barcode = f"SHARED-{uuid.uuid4().hex[:8]}"

    stock_1 = Stock(
        name="Riggs London Store 1",
        slug=f"riggs-store-1-{uuid.uuid4().hex[:6]}",
        store_id=seed_data["store_1"].store_id,
        barcode_id=shared_barcode,
        unit_price=500000,
        quantities=20.0,
        unit_in="piece",
        deleted=False,
    )
    stock_2 = Stock(
        name="Riggs London Store 2",
        slug=f"riggs-store-2-{uuid.uuid4().hex[:6]}",
        store_id=seed_data["store_2"].store_id,
        barcode_id=shared_barcode,
        unit_price=600000,
        quantities=15.0,
        unit_in="piece",
        deleted=False,
    )

    db_session.add(stock_1)
    db_session.add(stock_2)
    await db_session.flush()

    assert stock_1.id is not None
    assert stock_2.id is not None
    assert stock_1.barcode_id == stock_2.barcode_id
    assert stock_1.store_id != stock_2.store_id

    # Same store adding same barcode must be blocked
    from sqlalchemy.exc import IntegrityError
    stock_duplicate_same_store = Stock(
        name="Riggs London Store 1 Duplicate",
        slug=f"riggs-store-1-dup-{uuid.uuid4().hex[:6]}",
        store_id=seed_data["store_1"].store_id,
        barcode_id=shared_barcode,
        unit_price=500000,
        quantities=5.0,
        unit_in="piece",
        deleted=False,
    )
    db_session.add(stock_duplicate_same_store)
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()

