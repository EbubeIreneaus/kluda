from pydantic import BaseModel
from datetime import datetime
import uuid


class AdminAuditLogCreate(BaseModel):
    action: str
    target_type: str
    target_id: uuid.UUID | None = None
    details: dict | None = None
    ip_address: str | None = None


class AdminAuditLogResponse(BaseModel):
    id: int
    log_id: uuid.UUID
    admin_id: uuid.UUID | None = None
    action: str
    target_type: str
    target_id: uuid.UUID | None = None
    details: dict | None = None
    ip_address: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
