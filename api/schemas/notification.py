from enum import Enum
from pydantic import BaseModel
from datetime import datetime
import uuid


class NotificationScope(str, Enum):
    PERSONAL = "personal"
    STORE = "store"
    GLOBAL = "global"


class NotificationRecipientType(str, Enum):
    STAFF = "staff"
    USER = "user"
    ADMIN = "admin"


class NotificationCreate(BaseModel):
    title: str
    message: str
    scope: NotificationScope = NotificationScope.PERSONAL
    target_id: uuid.UUID | None = None
    data: dict | None = None


class NotificationResponse(BaseModel):
    notification_id: uuid.UUID
    title: str
    message: str
    scope: NotificationScope
    target_id: uuid.UUID | None = None
    data: dict | None = None
    created_at: datetime
    is_read: bool = False

    class Config:
        from_attributes = True


class NotificationSubscriptionCreate(BaseModel):
    user_type: NotificationRecipientType = NotificationRecipientType.STAFF
    sub_info: dict


class NotificationSubscriptionResponse(BaseModel):
    id: int
    user_type: NotificationRecipientType
    user_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True
