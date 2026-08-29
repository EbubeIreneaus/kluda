from pydantic import BaseModel
from datetime import datetime
import uuid


class SystemSettingUpdate(BaseModel):
    value: dict
    description: str | None = None


class SystemSettingResponse(BaseModel):
    id: int
    key: str
    value: dict
    description: str | None = None
    updated_by: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
