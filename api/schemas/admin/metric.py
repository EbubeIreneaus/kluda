from pydantic import BaseModel
from datetime import datetime


class DailyPlatformMetricResponse(BaseModel):
    id: int
    date: datetime
    total_stores: int
    active_stores: int
    total_sales_count: int
    total_revenue_amount: int
    total_offline_synced_sales: int
    new_users_registered: int
    new_staff_created: int
    created_at: datetime

    class Config:
        from_attributes = True
