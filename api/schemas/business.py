from pydantic import Field, HttpUrl, BaseModel, ConfigDict
from enum import Enum
from datetime import datetime
import uuid
from .stock import StockResponse, SaleResponse


class StoreStatus(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"
    DELETED = "deleted"


class StoreBase(BaseModel):
    name: str = Field(min_length=3)
    category: str
    address: str
    website: HttpUrl | None = None


class StoreCreate(StoreBase):
    pass


class StoreUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3)
    category: str | None = None
    website: HttpUrl | None = None


class StoreResponseMini(StoreBase):
    model_config = ConfigDict(from_attributes=True)
    store_id: uuid.UUID
    status: StoreStatus
    created_at: datetime


class StoreResponseSingle(StoreBase):
    model_config = ConfigDict(from_attributes=True)
    store_id: uuid.UUID
    status: StoreStatus
    created_at: datetime
    sales: list[SaleResponse]
    stocks: list[StockResponse]
