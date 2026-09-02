from pydantic import BaseModel, ConfigDict
from enum import Enum
import uuid
from datetime import datetime


class PlanStatus(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


class PaymentChannel(str, Enum):
    PAYSTACK = "paystack"
    MONIFY = "monify"


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    DUE = "due"
    EXPIRED = "expired"


class PlanResponse(BaseModel):
    id: int
    slug: str
    name: str
    description: str
    # Amount in subunit (kobo for NGN)
    price: int
    interval: str = "monthly"
    store_limit: int | None = 0
    product_limit: int | None = 0
    sales_limit_per_month: int | None = 0
    analytics_read_per_month: int | None = 0
    status: PlanStatus
    paystack_planid: str | None = None

    model_config = ConfigDict(from_attributes=True)


class SubscriptionUsageResponse(BaseModel):
    stores_count: int = 0
    stores_limit: int = 1
    products_count: int = 0
    products_limit: int = 100
    monthly_sales_count: int = 0
    monthly_sales_limit: int = 500
    monthly_analytics_count: int = 0
    monthly_analytics_limit: int = 100


class CurrentSubscriptionResponse(BaseModel):
    subscription_id: uuid.UUID | None = None
    plan: PlanResponse
    status: SubscriptionStatus
    # Amount in subunit (kobo for NGN)
    amount: int
    next_renewal: datetime | None = None
    usage: SubscriptionUsageResponse
    is_owner: bool = True
    owner_name: str | None = None
    has_used_trial: bool = False
    quota_token: str | None = None
    max_offline_days: int = 3
    offline_lease_expires_at: int | None = None
    offline_disclaimer: str | None = None

    model_config = ConfigDict(from_attributes=True)


class SubscribeRequest(BaseModel):
    plan_slug: str


class SubscribeResponse(BaseModel):
    status: str
    redirect_url: str | None = None
    reference: str | None = None
    message: str


class CancelSubscriptionResponse(BaseModel):
    status: str
    message: str