"""Esquemas de catálogo e inventario — S2 (unidades, impuestos, artículos, lotes)."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------- Unidades de medida ----------
class UnidadMedidaBase(BaseModel):
    clave: str = Field(max_length=10)
    nombre: str = Field(max_length=50)
    permite_decimales: bool = False


class UnidadMedidaCreate(UnidadMedidaBase):
    pass


class UnidadMedidaRead(UnidadMedidaBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID


# ---------- Impuestos ----------
class ImpuestoBase(BaseModel):
    nombre: str = Field(max_length=50)
    tipo: str = Field(pattern="^(iva|ieps|exento)$")
    tasa: Decimal = Field(max_digits=5, decimal_places=4, ge=0, le=1)


class ImpuestoCreate(ImpuestoBase):
    pass


class ImpuestoRead(ImpuestoBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID


# ---------- Artículos ----------
class ArticuloBase(BaseModel):
    sku: str = Field(max_length=50)
    descripcion: str
    unidad_medida_id: UUID
    impuesto_id: UUID | None = None
    precio_base: Decimal = Field(gt=0, max_digits=12, decimal_places=4)
    stock_minimo: Decimal = Field(default=Decimal("10.000"), max_digits=12, decimal_places=3)
    specs: dict = Field(default_factory=dict)
    activo_web: bool = True


class ArticuloCreate(ArticuloBase):
    pass


class ArticuloUpdate(BaseModel):
    descripcion: str | None = None
    precio_base: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=4)
    stock_minimo: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=3)
    activo_web: bool | None = None
    specs: dict | None = None


class ArticuloRead(ArticuloBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    stock_actual: Decimal
    stock_reservado: Decimal


# ---------- Lotes ----------
class LoteBase(BaseModel):
    articulo_id: UUID
    numero_lote: str = Field(max_length=50)
    fecha_vencimiento: date
    cantidad_actual: Decimal = Field(max_digits=12, decimal_places=3)
    costo_unitario: Decimal = Field(
        default=Decimal("0.0000"), ge=0, max_digits=12, decimal_places=4
    )


class LoteCreate(LoteBase):
    # Al recibir mercancía la cantidad debe ser positiva; al LEER un lote
    # agotado la cantidad es 0.000 (por eso la validación vive aquí, no en Base)
    cantidad_actual: Decimal = Field(gt=0, max_digits=12, decimal_places=3)
    sucursal_id: UUID | None = None


class LoteRead(LoteBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    estado: str
    sucursal_id: UUID | None = None
    cantidad_reservada: Decimal


class StockDisponible(BaseModel):
    articulo_id: UUID
    stock_actual: Decimal
    stock_reservado: Decimal
    stock_disponible: Decimal
