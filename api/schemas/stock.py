from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime
from typing import Literal, Any
import uuid
from schemas.user import CustomerResponse


class ProductImageCreate(BaseModel):
    src: str
    alt: str | None = None
    public_id: str | None = None


class ProductImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    src: str
    alt: str | None = None
    public_id: str | None = None
    created_at: datetime


class StockCreate(BaseModel):
    name: str
    barcode_id: str | None = None
    unit_price: int
    sku: str | None = None
    quantities: float = 1.0
    unit_in: Literal['piece', 'kg', 'g', 'litre', 'ml', 'pack', 'carton', 'dozen', 'bag'] = "piece"
    max_discount: int = 0
    description: str | None = None
    staff_note: str | None = None

    @field_validator('barcode_id', mode='before')
    @classmethod
    def normalize_barcode(cls, v: Any) -> str | None:
        if v is None:
            return None
        if isinstance(v, str):
            clean = v.strip()
            return clean if clean else None
        return v


class StockUpdate(BaseModel):
    name: str | None = None
    barcode_id: str | None = None
    unit_price: int | None = None
    sku: str | None = None
    quantities: float | None = None
    unit_in: Literal['piece', 'kg', 'g', 'litre', 'ml', 'pack', 'carton', 'dozen', 'bag'] | None = None
    max_discount: int | None = None
    description: str | None = None
    staff_note: str | None = None
    deleted: bool | None = None

    @field_validator('barcode_id', mode='before')
    @classmethod
    def normalize_barcode(cls, v: Any) -> str | None:
        if v is None:
            return None
        if isinstance(v, str):
            clean = v.strip()
            return clean if clean else None
        return v


class StockResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    slug: str
    barcode_id: str | None = None
    unit_price: int
    sku: str | None = None
    quantities: float
    unit_in: str
    max_discount: int
    description: str | None = None
    staff_note: str | None = None
    deleted: bool
    created_at: datetime
    updated_at: datetime


class StockHistoryCreate(BaseModel):
    stock_slug: str
    quantity: float
    action_type: Literal['addition', 'subtract'] = "addition"
    reason: Literal['restock', 'damage', 'adjustment', 'return'] = "restock"
    note: str | None = None


class StockHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sid: uuid.UUID
    stock_slug: str
    quantity: float
    action_type: str
    reason: str
    note: str | None = None
    staff_id: str | None = None
    store_id: uuid.UUID
    created_at: datetime


# --- Sale & Sale Item Schemas ---

class SaleItemCreate(BaseModel):
    stock_slug: str
    amount: int  # in kobo/cent
    quantities: float = 1.0


class SaleItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    stock_slug: str
    amount: int
    quantities: float
    stock: StockResponse | None = None


class SaleCreate(BaseModel):
    items: list[SaleItemCreate]
    discount: int = 0
    customer_id: uuid.UUID | None = None
    payment_method: Literal['cash', 'pos', 'debt', 'transfer', 'online']
    amount_recived: int
    idempotency_key: uuid.UUID
    staff_note: str | None = None
    status: Literal['pending', 'completed', 'cancelled'] = "completed"


class SaleUpdate(BaseModel):
    discount: int | None = None
    payment_method: Literal['cash', 'pos', 'debt', 'transfer', 'online'] | None = None
    amount_recived: int | None = None
    staff_note: str | None = None
    status: Literal['pending', 'completed', 'cancelled'] | None = None


class SaleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sale_id: uuid.UUID
    items: list[SaleItemResponse] = []
    discount: int
    customer: CustomerResponse | None = None
    payment_method: str
    amount_recived: int
    staff_note: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime


# --- Barcode Schemas ---

class BarcodeCreate(BaseModel):
    barcode_id: str
    title: str
    image: str


class BarcodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    barcode_id: str
    title: str
    image: str
    created_at: datetime
