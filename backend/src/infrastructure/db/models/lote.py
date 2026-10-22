"""Inventario — tlotes, tmovinventario (canon Sección 2).

F20: la verdad dura del stock vive en tlotes; el hard-allocate FEFO al confirmar
pago es el ÚNICO punto que consume lotes.
"""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
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


class TLote(Base):
    __tablename__ = "tlotes"
    __table_args__ = (
        CheckConstraint(
            "estado IN ('disponible','parcial','agotado','vencido','devuelto')",
            name="ck_lote_estado",
        ),
        UniqueConstraint("papeleria_id", "numero_lote", name="uq_lote_tenant_numero"),
    )

    id: Mapped[str] = mapped_column(SAUuid, primary_key=True, default=uuid_v7)
    papeleria_id: Mapped[str] = mapped_column(
        SAUuid, ForeignKey("papelerias.id"), index=True, nullable=False
    )
    sucursal_id: Mapped[str | None] = mapped_column(
        SAUuid, ForeignKey("sucursales.id"), index=True, nullable=True
    )
    articulo_id: Mapped[str] = mapped_column(
        SAUuid, ForeignKey("tarticulos.id"), index=True, nullable=False
    )
    numero_lote: Mapped[str] = mapped_column(String(50), nullable=False)
    fecha_vencimiento: Mapped[datetime] = mapped_column(Date, nullable=False)
    costo_unitario: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), default=Decimal("0.0000")
    )
    cantidad_actual: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    cantidad_reservada: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=Decimal("0.000"))
    estado: Mapped[str] = mapped_column(String(15), default="disponible")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class TMovInventario(Base):
    __tablename__ = "tmovinventario"
    __table_args__ = (
        CheckConstraint(
            "tipo_movimiento IN ('entrada','salida','ajuste','reserva','liberacion',"
            "'transferencia')",
            name="ck_mov_tipo",
        ),
    )

    id: Mapped[str] = mapped_column(SAUuid, primary_key=True, default=uuid_v7)
    papeleria_id: Mapped[str] = mapped_column(
        SAUuid, ForeignKey("papelerias.id"), index=True, nullable=False
    )
    sucursal_id: Mapped[str | None] = mapped_column(
        SAUuid, ForeignKey("sucursales.id"), index=True, nullable=True
    )
    articulo_id: Mapped[str] = mapped_column(
        SAUuid, ForeignKey("tarticulos.id"), index=True, nullable=False
    )
    lote_id: Mapped[str | None] = mapped_column(SAUuid, ForeignKey("tlotes.id"), nullable=True)
    tipo_movimiento: Mapped[str] = mapped_column(String(15), nullable=False)
    cantidad: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    motivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
