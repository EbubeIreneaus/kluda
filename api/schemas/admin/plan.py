from datetime import datetime
from pydantic import BaseModel, ConfigDict
from schemas.subscription import PlanStatus


class PlanCreate(BaseModel):
    slug: str
    name: str
    description: str
    # amount in subunit (kobo for NGN)
    price: int
    interval: str = "monthly"
    store_limit: int | None = 0
    product_limit: int | None = 0
    sales_limit_per_month: int | None = 0
    analytics_read_per_month: int | None = 0
    status: PlanStatus = PlanStatus.AVAILABLE
    paystack_planid: str | None = None


class PlanUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    # amount in subunit (kobo for NGN)
    price: int | None = None
    interval: str | None = None
    store_limit: int | None = None
    product_limit: int | None = None
    sales_limit_per_month: int | None = None
    analytics_read_per_month: int | None = None
    status: PlanStatus | None = None
    paystack_planid: str | None = None


class PlanResponse(BaseModel):
    id: int
    slug: str
    name: str
    description: str
    # amount in subunit (kobo for NGN)
    price: int
    interval: str = "monthly"
    store_limit: int | None = 0
    product_limit: int | None = 0
    sales_limit_per_month: int | None = 0
    analytics_read_per_month: int | None = 0
    status: PlanStatus
    paystack_planid: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
