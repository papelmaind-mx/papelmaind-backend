"""Esquemas POS (S3) — venta transaccional idempotente (CONV-12/13)."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

MetodoPago = Literal["efectivo", "tarjeta", "transferencia", "spei", "mixto", "credito", "puntos"]
TipoPago = Literal["efectivo", "tarjeta", "transferencia", "puntos", "credito"]
OrigenVenta = Literal["pos", "rompefila", "ecommerce", "whatsapp", "kiosco"]


class SaleLineIn(BaseModel):
    """Partida de venta. precio_unitario opcional = override (precio negotiated)."""

    articulo_id: UUID
    cantidad: Decimal = Field(gt=0, max_digits=12, decimal_places=3)
    precio_unitario: Decimal | None = Field(
        default=None, gt=0, max_digits=12, decimal_places=2
    )


class PagoIn(BaseModel):
    tipo: TipoPago
    monto: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


class SaleCreate(BaseModel):
    """CONV-12: POS offline escribe IndexedDB con client_uuid v7 y sincroniza idempotente."""

    model_config = ConfigDict(extra="forbid")

    client_uuid: UUID
    items: list[SaleLineIn] = Field(min_length=1)
    metodo_pago: MetodoPago = "efectivo"
    pagos: list[PagoIn] = Field(default_factory=list)
    origen: OrigenVenta = "pos"
    cliente_rel_id: UUID | None = None
    sucursal_id: UUID | None = None
    estacion_id: UUID | None = None
    corte_id: UUID | None = None


class SaleLineOut(BaseModel):
    articulo_id: UUID
    lote_id: UUID | None = None
    cantidad: Decimal
    precio_unitario: Decimal
    subtotal: Decimal
    impuesto_id: UUID | None = None


class PagoOut(BaseModel):
    tipo: str
    monto: Decimal


class SaleOut(BaseModel):
    id: UUID
    folio: str | None
    client_uuid: UUID | None
    subtotal: Decimal
    impuestos: Decimal
    total: Decimal
    metodo_pago: str | None
    estado: str
    origen: str | None
    created_at: datetime | None = None
    items: list[SaleLineOut] = Field(default_factory=list)
    pagos: list[PagoOut] = Field(default_factory=list)
    replayed: bool = False
