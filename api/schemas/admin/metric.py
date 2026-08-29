from pydantic import BaseModel
from datetime import datetime


class DailyPlatformMetricResponse(BaseModel):
    id: int
    date: datetime
    total_merchants: int
    new_merchants_today: int
    total_stores: int
    active_stores: int
    total_staff: int
    total_products: int
    total_transactions: int
    total_gmv: int
    total_tickets_open: int
    total_emails_unread: int
    created_at: datetime

    class Config:
        from_attributes = True
