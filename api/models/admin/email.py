from typing import Literal
from sqlalchemy import Text, DateTime, String, Enum, Integer, func, UUID, ForeignKey, JSON
from sqlalchemy.orm import MappedColumn, mapped_column, relationship
from schemas.admin.email import EmailThreadStatus, EmailCampaignStatus, MailboxType
from pydantic import EmailStr
from ..config import Base
from datetime import datetime
import uuid


class EmailMailbox(Base):
    __tablename__ = "email_mailboxes"
    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)
    mailbox_id: MappedColumn[uuid.UUID] = mapped_column(UUID, default=uuid.uuid4, index=True, unique=True)
    name: MappedColumn[str] = mapped_column(String(100), nullable=False)
    email: MappedColumn[EmailStr] = mapped_column(String(255), unique=True, index=True, nullable=False)
    type: MappedColumn[MailboxType] = mapped_column(Enum(MailboxType), default=MailboxType.SHARED, index=True)
    owner_admin_id: MappedColumn[uuid.UUID | None] = mapped_column(UUID, ForeignKey("admins.admin_id", ondelete="CASCADE"), nullable=True, index=True)
    allowed_admin_ids: MappedColumn[list[str]] = mapped_column(JSON, default=list)
    created_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    threads: MappedColumn[list["EmailThread"]] = relationship(back_populates="mailbox", cascade="all, delete-orphan")


class EmailCampaign(Base):
    __tablename__ = "email_campaigns"
    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)
    campaign_id: MappedColumn[uuid.UUID] = mapped_column(UUID, default=uuid.uuid4, index=True, unique=True)
    title: MappedColumn[str] = mapped_column(String(255), nullable=False)
    subject: MappedColumn[str] = mapped_column(String(255), nullable=False)
    sender: MappedColumn[EmailStr] = mapped_column(String(255), nullable=False)
    body: MappedColumn[str] = mapped_column(Text, nullable=False)
    status: MappedColumn[EmailCampaignStatus] = mapped_column(Enum(EmailCampaignStatus), default=EmailCampaignStatus.DRAFT, index=True)
    target_audience: MappedColumn[str] = mapped_column(String(100), default="all")
    total_recipients: MappedColumn[int] = mapped_column(Integer, default=0)
    total_delivered: MappedColumn[int] = mapped_column(Integer, default=0)
    total_failed: MappedColumn[int] = mapped_column(Integer, default=0)
    scheduled_at: MappedColumn[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: MappedColumn[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class EmailThread(Base):
    __tablename__ = "email_threads"
    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)
    thread_id: MappedColumn[uuid.UUID] = mapped_column(UUID, default=uuid.uuid4, index=True, unique=True)
    mailbox_id: MappedColumn[uuid.UUID | None] = mapped_column(UUID, ForeignKey("email_mailboxes.mailbox_id", ondelete="SET NULL"), nullable=True, index=True)
    mailbox: MappedColumn["EmailMailbox | None"] = relationship(back_populates="threads")
    customer_email: MappedColumn[EmailStr] = mapped_column(String(255), nullable=False, index=True)
    to: MappedColumn[EmailStr] = mapped_column(String(255), nullable=False, index=True)
    subject: MappedColumn[str] = mapped_column(String(255), nullable=False)
    snippet: MappedColumn[str | None] = mapped_column(String(500), nullable=True)
    status: MappedColumn[EmailThreadStatus] = mapped_column(Enum(EmailThreadStatus), default=EmailThreadStatus.UNREAD, index=True)
    created_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_message_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), index=True)
    messages: MappedColumn[list["EmailMessages"]] = relationship(back_populates="thread", cascade="all, delete-orphan")


class EmailMessages(Base):
    __tablename__ = "email_messages"
    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)
    message_id: MappedColumn[uuid.UUID] = mapped_column(UUID, default=uuid.uuid4, index=True, unique=True)
    thread_id: MappedColumn[uuid.UUID] = mapped_column(UUID, ForeignKey("email_threads.thread_id", ondelete="CASCADE"), nullable=False, index=True)
    # mail_id is the email Message=ID (RFC)
    mail_id: MappedColumn[str | None] = mapped_column(String(255), nullable=True, index=True)
    resend_id: MappedColumn[str | None] = mapped_column(String(255), nullable=True, index=True)
    thread: MappedColumn['EmailThread'] = relationship(back_populates="messages")
    recipients: MappedColumn[EmailStr] = mapped_column(String(255), nullable=False)
    sender: MappedColumn[EmailStr] = mapped_column(String(255), nullable=False)
    body: MappedColumn[str] = mapped_column(Text, nullable=False)
    direction: MappedColumn[Literal['incoming', 'outgoing']] = mapped_column(String(20), nullable=False, index=True, default="incoming")
    created_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    in_reply_to: MappedColumn[str | None] = mapped_column(String(255), nullable=True)