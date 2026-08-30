from enum import Enum
from pydantic import BaseModel, EmailStr
from datetime import datetime
import uuid


class EmailThreadStatus(str, Enum):
    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"
    SPAM = "spam"
    DELETED = "deleted"


class EmailCampaignStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"


class MailboxType(str, Enum):
    PERSONAL = "personal"
    SHARED = "shared"


class MailboxCreate(BaseModel):
    name: str
    email: EmailStr
    type: MailboxType = MailboxType.SHARED
    owner_admin_id: uuid.UUID | None = None
    allowed_admin_ids: list[uuid.UUID] = []


class MailboxUpdate(BaseModel):
    name: str | None = None
    allowed_admin_ids: list[uuid.UUID] | None = None


class MailboxResponse(BaseModel):
    id: int
    mailbox_id: uuid.UUID
    name: str
    email: str
    type: MailboxType
    owner_admin_id: uuid.UUID | None = None
    allowed_admin_ids: list[uuid.UUID] = []
    created_at: datetime

    class Config:
        from_attributes = True


class EmailCampaignCreate(BaseModel):
    title: str
    subject: str
    sender: EmailStr
    body: str
    target_audience: str = "all_merchants"
    scheduled_at: datetime | None = None


class EmailCampaignUpdate(BaseModel):
    title: str | None = None
    subject: str | None = None
    sender: EmailStr | None = None
    body: str | None = None
    target_audience: str | None = None
    scheduled_at: datetime | None = None


class EmailCampaignResponse(BaseModel):
    id: int
    campaign_id: uuid.UUID
    title: str
    subject: str
    sender: str
    body: str
    status: EmailCampaignStatus
    target_audience: str
    total_recipients: int
    total_delivered: int
    total_failed: int
    scheduled_at: datetime | None = None
    sent_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmailMessageCreate(BaseModel):
    body: str


class EmailComposeRequest(BaseModel):
    mailbox_id: uuid.UUID
    to_email: EmailStr
    subject: str
    body: str


class EmailMessageResponse(BaseModel):
    id: int
    message_id: uuid.UUID
    thread_id: uuid.UUID
    mail_id: str | None = None
    recipients: str
    sender: str
    body: str
    direction: str
    in_reply_to: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class EmailThreadResponse(BaseModel):
    id: int
    thread_id: uuid.UUID
    mailbox_id: uuid.UUID | None = None
    customer_email: str
    to: str
    subject: str
    snippet: str | None = None
    status: EmailThreadStatus
    created_at: datetime
    last_message_at: datetime
    messages: list[EmailMessageResponse] = []

    class Config:
        from_attributes = True