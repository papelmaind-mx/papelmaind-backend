"""Ventas + Outbox + DLQ (S3 POS transaccional).

OutboxEvento cumple F17: flags SEPARADOS por consumidor
(publicado_kafka + procesado_loyalty), nunca un 'procesado' único.
CONV-13: idempotencia vía UNIQUE(client_uuid) en BD, NUNCA SELECT previo.
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
    Index,
    Numeric,
    String,
)
from sqlalchemy import Uuid as SAUuid
from sqlalchemy.orm import Mapped, mapped_column

from src.core.security import uuid_v7
from src.infrastructure.db.models.base import Base


class OutboxEvento(Base):
    """Transactional Outbox — F17: flags separados por consumidor."""

    __tablename__ = "outbox_eventos"

    id: Mapped[str] = mapped_column(SAUuid, primary_key=True, default=uuid_v7)
    papeleria_id: Mapped[str] = mapped_column(
        SAUuid, ForeignKey("papelerias.id"), index=True, nullable=False
    )
    tipo: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    aggregate_type: Mapped[str] = mapped_column(String(50), nullable=False)
    aggregate_id: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    # canon outbox_eventos: client_uuid UNIQUE (idempotencia de publicación)
    client_uuid: Mapped[str | None] = mapped_column(SAUuid, nullable=True, unique=True)
    # F17: flags separados — jamás regresar a un 'procesado' único
    publicado_kafka: Mapped[bool] = mapped_column(Boolean, default=False)
    procesado_loyalty: Mapped[bool] = mapped_column(Boolean, default=False)
    intentos: Mapped[int] = mapped_column(default=0)
    error_ultimo: Mapped[str | None] = mapped_column(String(500), nullable=True)
    procesado_en: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class TDlqEvento(Base):
    """DLQ — eventos con error terminal de dominio (canon tdlq_eventos)."""

    __tablename__ = "tdlq_eventos"
    __table_args__ = (
        CheckConstraint(
            "estado IN ('pendiente','reintentado','descartado','resuelto')",
            name="ck_dlq_estado",
        ),
        Index(
            "idx_dlq_pendientes",
            "first_failed_at",
            postgresql_where="estado = 'pendiente'",
        ),
    )

    id: Mapped[str] = mapped_column(SAUuid, primary_key=True, default=uuid_v7)
    outbox_evento_id: Mapped[str] = mapped_column(SAUuid, unique=True, nullable=False)
    papeleria_id: Mapped[str | None] = mapped_column(
        SAUuid, ForeignKey("papelerias.id"), nullable=True
    )
    event_type: Mapped[str | None] = mapped_column(String(100))
    aggregate_type: Mapped[str | None] = mapped_column(String(50))
    aggregate_id: Mapped[str | None] = mapped_column(String(100))
    payload: Mapped[dict | None] = mapped_column(JSON)
    error_ultimo: Mapped[str | None] = mapped_column(String(500))
    historial_intentos: Mapped[list] = mapped_column(JSON, default=list)
    trace_id: Mapped[str | None] = mapped_column(String(64))
    estado: Mapped[str] = mapped_column(String(12), default="pendiente")
    motivo_descarte: Mapped[str | None] = mapped_column(String(200))
    descartado_por: Mapped[str | None] = mapped_column(SAUuid, nullable=True)
    descartado_en: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    first_failed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class TVenta(Base):
    """S3: POS transaccional. CONV-12/13: client_uuid v7 UNIQUE → sync offline idempotente."""

    __tablename__ = "tventas"
    __table_args__ = (
        CheckConstraint(
            "metodo_pago IN ('efectivo','tarjeta','transferencia','spei','mixto',"
            "'credito','puntos')",
            name="ck_venta_metodo_pago",
        ),
        CheckConstraint(
            "origen IN ('pos','rompefila','ecommerce','whatsapp','kiosco')",
            name="ck_venta_origen",
        ),
    )

    id: Mapped[str] = mapped_column(SAUuid, primary_key=True, default=uuid_v7)
    papeleria_id: Mapped[str] = mapped_column(
        SAUuid, ForeignKey("papelerias.id"), index=True, nullable=False
    )
    sucursal_id: Mapped[str | None] = mapped_column(SAUuid, nullable=True)
    estacion_id: Mapped[str | None] = mapped_column(SAUuid, nullable=True)
    cliente_rel_id: Mapped[str | None] = mapped_column(SAUuid, nullable=True)
    corte_id: Mapped[str | None] = mapped_column(SAUuid, nullable=True)
    folio: Mapped[str | None] = mapped_column(String(30))
    client_uuid: Mapped[str | None] = mapped_column(SAUuid, unique=True)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    impuestos: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    metodo_pago: Mapped[str | None] = mapped_column(String(15))
    estado: Mapped[str] = mapped_column(String(20), default="completada")
    origen: Mapped[str | None] = mapped_column(String(12))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class TDetalleVenta(Base):
    """Partidas de la venta — lote_id queda fijado por el hard-allocate FEFO."""

    __tablename__ = "tdetallesventa"

    id: Mapped[str] = mapped_column(SAUuid, primary_key=True, default=uuid_v7)
    papeleria_id: Mapped[str] = mapped_column(
        SAUuid, ForeignKey("papelerias.id"), index=True, nullable=False
    )
    venta_id: Mapped[str] = mapped_column(
        SAUuid, ForeignKey("tventas.id"), index=True, nullable=False
    )
    articulo_id: Mapped[str] = mapped_column(
        SAUuid, ForeignKey("tarticulos.id"), nullable=False
    )
    lote_id: Mapped[str | None] = mapped_column(
        SAUuid, ForeignKey("tlotes.id"), nullable=True
    )
    cantidad: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    impuesto_id: Mapped[str | None] = mapped_column(
        SAUuid, ForeignKey("timpuestos.id"), nullable=True
    )


class TPagoVenta(Base):
    """Pagos aplicados a una venta (soporta mixto: efectivo + tarjeta + puntos)."""

    __tablename__ = "tpagosventa"
    __table_args__ = (
        CheckConstraint(
            "tipo IN ('efectivo','tarjeta','transferencia','puntos','credito')",
            name="ck_pago_tipo",
        ),
    )

    id: Mapped[str] = mapped_column(SAUuid, primary_key=True, default=uuid_v7)
    papeleria_id: Mapped[str] = mapped_column(
        SAUuid, ForeignKey("papelerias.id"), index=True, nullable=False
    )
    venta_id: Mapped[str] = mapped_column(
        SAUuid, ForeignKey("tventas.id"), index=True, nullable=False
    )
    tipo: Mapped[str] = mapped_column(String(15), nullable=False)
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)


class THistorialVentas(Base):
    """Auditoría de cambios de estado de la venta (canon thistorialventas)."""

    __tablename__ = "thistorialventas"

    id: Mapped[str] = mapped_column(SAUuid, primary_key=True, default=uuid_v7)
    venta_id: Mapped[str] = mapped_column(
        SAUuid, ForeignKey("tventas.id"), index=True, nullable=False
    )
    estado_anterior: Mapped[str | None] = mapped_column(String(20))
    estado_nuevo: Mapped[str] = mapped_column(String(20), nullable=False)
    motivo: Mapped[str | None] = mapped_column(String(200))
