from pydantic import BaseModel
from datetime import datetime
import uuid


class AdminMerchantListItem(BaseModel):
    id: int
    user_id: uuid.UUID
    fullname: str
    email: str
    phone: str | None = None
    status: str
    store_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class AdminMerchantSubscriptionInfo(BaseModel):
    plan_slug: str
    plan_name: str
    interval: str | None = None
    status: str
    amount: int
    is_trial: bool = False
    next_renewal: datetime | None = None


class AdminMerchantStoreSummary(BaseModel):
    store_id: uuid.UUID
    name: str
    category: str | None = None
    status: str
    staff_count: int = 0
    product_count: int = 0
    total_sales_count: int = 0
    total_revenue: int = 0
    created_at: datetime


class AdminMerchantDetailResponse(BaseModel):
    id: int
    user_id: uuid.UUID
    fullname: str
    email: str
    phone: str | None = None
    status: str
    subscription: AdminMerchantSubscriptionInfo | None = None
    stores: list[AdminMerchantStoreSummary] = []
    created_at: datetime
    last_login: datetime | None = None

    class Config:
        from_attributes = True


class AdminMerchantStatusUpdateRequest(BaseModel):
    status: str
    reason: str | None = None
