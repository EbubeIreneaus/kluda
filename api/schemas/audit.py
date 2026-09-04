from pydantic import BaseModel
from datetime import datetime
import uuid


class StoreAuditLogResponse(BaseModel):
    id: int
    log_id: uuid.UUID
    store_id: uuid.UUID
    actor_id: uuid.UUID | None = None
    actor_name: str | None = None
    actor_email: str | None = None
    actor_role: str | None = None
    action: str
    target_type: str
    target_id: str | None = None
    target_name: str | None = None
    details: dict | None = None
    ip_address: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class StoreAuditLogPaginationResponse(BaseModel):
    items: list[StoreAuditLogResponse]
    total: int
    limit: int
    offset: int
