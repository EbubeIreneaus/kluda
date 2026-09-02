from pydantic import HttpUrl
from typing import TYPE_CHECKING
from sqlalchemy import Text
from sqlalchemy import JSON
from typing import Literal
from schemas.user import CustomerStatus
from pydantic import EmailStr
from .config import Base
from sqlalchemy.orm import MappedColumn, mapped_column, relationship
from sqlalchemy import DateTime, String, Enum, Integer, func, UUID, ForeignKey
from schemas.user import StaffStatus, StaffPermission
from schemas.business import StoreStatus
from datetime import datetime
import uuid

if TYPE_CHECKING:
    from .user import User, Customer, StoreMember
    from .stock import Stock, Sale, StockHistory


class Store(Base):
    __tablename__="stores"
    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)
    store_id: MappedColumn[uuid.UUID] = mapped_column(UUID, default=uuid.uuid4, unique=True, index=True)
    name: MappedColumn[str] = mapped_column(String, nullable=False)
    members: MappedColumn[list['StoreMember']] = relationship(back_populates="store", cascade="all, delete-orphan")
    user_id: MappedColumn[uuid.UUID] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), index=True)
    user: MappedColumn['User'] = relationship(back_populates="stores")
    stocks: MappedColumn[list['Stock']]=relationship(back_populates="store", cascade="all, delete-orphan")
    sales: MappedColumn[list['Sale']]=relationship(back_populates="store", cascade="all, delete-orphan")
    category: MappedColumn[str] = mapped_column(String)
    address: MappedColumn[str] = mapped_column(String)
    stock_histories: MappedColumn[list['StockHistory']] = relationship(back_populates="store", cascade="all, delete-orphan")
    status: MappedColumn[StoreStatus] = mapped_column(Enum(StoreStatus), default=StoreStatus.ACTIVE)
    delete_reason: MappedColumn[str | None] = mapped_column(String, nullable=True)
    website: MappedColumn[HttpUrl | None] = mapped_column(String, nullable=True)
    customers: MappedColumn[list['Customer']] = relationship(back_populates="store")
    created_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), server_onupdate=func.now())