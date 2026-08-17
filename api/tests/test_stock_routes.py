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
