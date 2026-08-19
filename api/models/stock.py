from sqlalchemy import UUID
import uuid
from sqlalchemy import Boolean
from sqlalchemy.orm import relationship
from typing import Literal
from sqlalchemy import Numeric
from pydantic import EmailStr
from .config import Base
from sqlalchemy.orm import MappedColumn, mapped_column
from sqlalchemy import DateTime, String, Enum, Integer, func, ForeignKey
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user import Customer, Staff
    from .business import Store


class Stock(Base):
    __tablename__ = "stocks"
    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)
    name: MappedColumn[str] = mapped_column(String)
    slug: MappedColumn[str] = mapped_column(String, unique=True)
    store_id: MappedColumn[uuid.UUID] = mapped_column(
        ForeignKey("stores.store_id", ondelete="CASCADE"),
        index=True
    )
    store: MappedColumn["Store"] = relationship(back_populates="stocks")
    barcode_id: MappedColumn[str | None] = mapped_column(
        String, nullable=True, unique=True
    )
    unit_price: MappedColumn[int] = mapped_column(
        Integer, default=1000
    )  # 100kobo * 10 = 10naira
    sku: MappedColumn[str | None] = mapped_column(String, nullable=True)
    quantities: MappedColumn[float] = mapped_column(
        Numeric(precision=8, scale=2), default=1
    )
    unit_in: MappedColumn[
        Literal["piece", "kg", "g", "litre", "ml", "pack", "carton", "dozen", "bag"]
    ] = mapped_column(String(10), default="piece")
    max_discount: MappedColumn[int] = mapped_column(Integer, default=0)
    images: MappedColumn[list["Images"]] = relationship(cascade="all, delete-orphan")
    description: MappedColumn[str | None] = mapped_column(String, nullable=True)
    staff_note: MappedColumn[str | None] = mapped_column(String, nullable=True)
    deleted: MappedColumn[bool] = mapped_column(Boolean, default=False)
    deleted_at: MappedColumn[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: MappedColumn[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: MappedColumn[datetime] = mapped_column(
        DateTime(timezone=True), server_onupdate=func.now(), server_default=func.now()
    )

class StockHistory(Base):
    __tablename__="stock_histories"
    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)
    sid: MappedColumn[uuid.UUID] = mapped_column(UUID, default=uuid.uuid4, unique=True, index=True)
    stock_slug: MappedColumn[str] = mapped_column(
        ForeignKey("stocks.slug"), nullable=False, index=True
    )
    stock: MappedColumn["Stock"] = relationship()
    quantity: MappedColumn[float] = mapped_column(Numeric(precision=8, scale=2), default=1) 
    staff_id: MappedColumn[str] = mapped_column(ForeignKey("staffs.staff_id"), nullable=True)
    store_id: MappedColumn[uuid.UUID] = mapped_column(
        ForeignKey("stores.store_id", ondelete="CASCADE"),
        index=True
    )
    store: MappedColumn["Store"] = relationship(back_populates="stock_histories")
    staff: MappedColumn['Staff'] = relationship()
    reason: MappedColumn[
        Literal['restock', "damage", "adjustment", "return"]
    ] = mapped_column(String(20), default="restock")
    action_type: MappedColumn[Literal['addition', 'subtract']] = mapped_column(String(20), default="addition")
    note: MappedColumn[str | None] = mapped_column(String, nullable=True)
    created_at: MappedColumn[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class SaleItem(Base):
    __tablename__ = "sale_items"
    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)
    stock_slug: MappedColumn[str] = mapped_column(
        ForeignKey("stocks.slug"), nullable=False
    )
    stock: MappedColumn["Stock"] = relationship()
    amount: MappedColumn[int] = mapped_column(Integer)
    quantities: MappedColumn[float] = mapped_column(
        Numeric(precision=8, scale=2), default=1
    )
    sale_id: MappedColumn[uuid.UUID] = mapped_column(
        ForeignKey("sales.sale_id"), nullable=False
    )
    sale: MappedColumn["Sale"] = relationship(back_populates="items")


class Sale(Base):
    __tablename__ = "sales"
    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)
    sale_id: MappedColumn[uuid.UUID] = mapped_column(
        UUID, default=uuid.uuid4, unique=True
    )
    items: MappedColumn[list[SaleItem]] = relationship(back_populates="sale")
    store_id: MappedColumn[uuid.UUID] = mapped_column(
        ForeignKey("stores.store_id", ondelete="CASCADE"),
        index=True
    )
    store: MappedColumn["Store"] = relationship(back_populates="sales")
    discount: MappedColumn[int] = mapped_column(Integer, default=0)
    customer_id: MappedColumn[str | None] = mapped_column(
        ForeignKey("customers.customer_id"), nullable=True
    )
    customer: MappedColumn["Customer"] = relationship()
    payment_method: MappedColumn[
        Literal["cash", "pos", "debt", "transfer", "online"]
    ] = mapped_column(String(10))
    amount_recived: MappedColumn[int] = mapped_column(Integer)
    idempotency_key: MappedColumn[uuid.UUID] = mapped_column(
        UUID, unique=True, index=True
    )
    staff_note: MappedColumn[str | None] = mapped_column(String, nullable=True)
    status: MappedColumn[Literal["pending", "completed", "cancelled"]] = mapped_column(
        String(10)
    )
    created_at: MappedColumn[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: MappedColumn[datetime] = mapped_column(
        DateTime(timezone=True), server_onupdate=func.now(), server_default=func.now()
    )


class Images(Base):
    __tablename__ = "product_images"
    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)
    stock_slug: MappedColumn[str] = mapped_column(ForeignKey("stocks.slug"))
    src: MappedColumn[str] = mapped_column(String)
    alt: MappedColumn[str | None] = mapped_column(String, nullable=True)
    public_id: MappedColumn[str | None] = mapped_column(String, nullable=True)
    created_at: MappedColumn[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Barcode(Base):
    __tablename__ = "store_barcodes"
    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)
    barcode_id: MappedColumn[str] = mapped_column(String, nullable=False, unique=True)
    title: MappedColumn[str] = mapped_column(String)
    image: MappedColumn[str] = mapped_column(String)
    created_at: MappedColumn[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
