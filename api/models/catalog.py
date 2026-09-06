from datetime import datetime
from typing import Literal
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import MappedColumn, mapped_column, relationship

from .config import Base


class CatalogTemplate(Base):
    __tablename__ = "catalog_templates"

    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)
    name: MappedColumn[str] = mapped_column(String, nullable=False)
    slug: MappedColumn[str] = mapped_column(
        String, unique=True, index=True, nullable=False
    )
    description: MappedColumn[str | None] = mapped_column(String, nullable=True)
    icon: MappedColumn[str | None] = mapped_column(String(50), default="package")
    is_active: MappedColumn[bool] = mapped_column(Boolean, default=True, index=True)
    sort_order: MappedColumn[int] = mapped_column(Integer, default=0)
    total_imports: MappedColumn[int] = mapped_column(Integer, default=0)

    items: MappedColumn[list["CatalogItem"]] = relationship(
        "CatalogItem",
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="CatalogItem.id",
    )

    created_at: MappedColumn[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: MappedColumn[datetime] = mapped_column(
        DateTime(timezone=True), server_onupdate=func.now(), server_default=func.now()
    )


class CatalogItem(Base):
    __tablename__ = "catalog_items"
    __table_args__ = (
        Index("ix_catalog_items_template_barcode", "template_id", "barcode"),
    )

    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)
    template_id: MappedColumn[int] = mapped_column(
        ForeignKey("catalog_templates.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    template: MappedColumn["CatalogTemplate"] = relationship(
        "CatalogTemplate", back_populates="items"
    )

    name: MappedColumn[str] = mapped_column(String, nullable=False, index=True)
    barcode: MappedColumn[str | None] = mapped_column(String, nullable=True, index=True)
    category: MappedColumn[str] = mapped_column(
        String, nullable=False, default="General", index=True
    )

    suggested_price: MappedColumn[int] = mapped_column(Integer, default=0)
    cost_price: MappedColumn[int] = mapped_column(Integer, default=0)

    unit_in: MappedColumn[
        Literal["piece", "kg", "g", "litre", "ml", "pack", "carton", "dozen", "bag", "sachet"]
    ] = mapped_column(String(10), default="piece")

    description: MappedColumn[str | None] = mapped_column(String, nullable=True)
    is_active: MappedColumn[bool] = mapped_column(Boolean, default=True)

    created_at: MappedColumn[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: MappedColumn[datetime] = mapped_column(
        DateTime(timezone=True), server_onupdate=func.now(), server_default=func.now()
    )
