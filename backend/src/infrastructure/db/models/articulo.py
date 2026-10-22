"""Catálogo — tunidadesmedida, timpuestos, tarticulos (canon Sección 2).

CONV-17: CATÁLOGO por tenant (sin sucursal_id). STOCK por sucursal (tlotes).
UNIQUE(papeleria_id, sku) en tarticulos.
"""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import Uuid as SAUuid
from sqlalchemy.orm import Mapped, mapped_column

from src.core.security import uuid_v7
from src.infrastructure.db.models.base import Base


class TUnidadMedida(Base):
    __tablename__ = "tunidadesmedida"
    __table_args__ = (UniqueConstraint("papeleria_id", "clave", name="uq_um_tenant_clave"),)

    id: Mapped[str] = mapped_column(SAUuid, primary_key=True, default=uuid_v7)
    papeleria_id: Mapped[str] = mapped_column(
        SAUuid, ForeignKey("papelerias.id"), index=True, nullable=False
    )
    clave: Mapped[str] = mapped_column(String(10), nullable=False)
    nombre: Mapped[str] = mapped_column(String(50), nullable=False)
    permite_decimales: Mapped[bool] = mapped_column(Boolean, default=False)


class TImpuesto(Base):
    __tablename__ = "timpuestos"
    __table_args__ = (
        CheckConstraint("tipo IN ('iva','ieps','exento')", name="ck_impuesto_tipo"),
    )

    id: Mapped[str] = mapped_column(SAUuid, primary_key=True, default=uuid_v7)
    papeleria_id: Mapped[str] = mapped_column(
        SAUuid, ForeignKey("papelerias.id"), index=True, nullable=False
    )
    nombre: Mapped[str] = mapped_column(String(50), nullable=False)
    tipo: Mapped[str] = mapped_column(String(10), nullable=False)
    tasa: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)


class TArticulo(Base):
    __tablename__ = "tarticulos"
    __table_args__ = (UniqueConstraint("papeleria_id", "sku", name="uq_articulo_tenant_sku"),)

    id: Mapped[str] = mapped_column(SAUuid, primary_key=True, default=uuid_v7)
    papeleria_id: Mapped[str] = mapped_column(
        SAUuid, ForeignKey("papelerias.id"), index=True, nullable=False
    )
    sku: Mapped[str] = mapped_column(String(50), nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    specs: Mapped[dict] = mapped_column(JSON, default=dict)
    unidad_medida_id: Mapped[str] = mapped_column(
        SAUuid, ForeignKey("tunidadesmedida.id"), nullable=False
    )
    impuesto_id: Mapped[str | None] = mapped_column(
        SAUuid, ForeignKey("timpuestos.id"), nullable=True
    )
    precio_base: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), nullable=False, default=Decimal("0.0000")
    )
    activo_web: Mapped[bool] = mapped_column(Boolean, default=True)
    stock_actual: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=Decimal("0.000"))
    stock_reservado: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=Decimal("0.000"))
    # Canon: default 10 · o dinámico: demanda30d × lead_time × 1.5
    stock_minimo: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=Decimal("10.000"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
