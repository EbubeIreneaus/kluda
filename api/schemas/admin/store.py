from pydantic import BaseModel
from datetime import datetime
import uuid


class AdminStoreListItem(BaseModel):
    id: int
    store_id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    category: str | None = None
    status: str
    staff_count: int = 0
    product_count: int = 0
    total_sales_count: int = 0
    total_revenue: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class AdminStoreStaffItem(BaseModel):
    id: int
    user_id: uuid.UUID
    fullname: str
    email: str
    role: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class AdminStoreDetailResponse(BaseModel):
    id: int
    store_id: uuid.UUID
    owner_id: uuid.UUID
    owner_name: str | None = None
    owner_email: str | None = None
    name: str
    address: str | None = None
    category: str | None = None
    currency: str = "NGN"
    status: str
    staff_count: int = 0
    product_count: int = 0
    customer_count: int = 0
    total_sales_count: int = 0
    total_revenue: int = 0
    staff: list[AdminStoreStaffItem] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AdminStoreStatusUpdateRequest(BaseModel):
    status: str
    reason: str | None = None
