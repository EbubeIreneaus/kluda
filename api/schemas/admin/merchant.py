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


class AdminMerchantDetailResponse(BaseModel):
    id: int
    user_id: uuid.UUID
    fullname: str
    email: str
    phone: str | None = None
    status: str
    stores: list[dict] = []
    created_at: datetime
    last_login: datetime | None = None

    class Config:
        from_attributes = True


class AdminMerchantStatusUpdateRequest(BaseModel):
    status: str
    reason: str | None = None
