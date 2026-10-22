"""Registro central de modelos — canon: '119 modelos' al completar P0-P3.

S1: tenancy + usuarios + sesiones · S2: catálogo + impuestos + lotes · S3: ventas + outbox.
"""
from src.infrastructure.db.models.articulo import TArticulo, TImpuesto, TUnidadMedida
from src.infrastructure.db.models.base import Base
from src.infrastructure.db.models.lote import TLote, TMovInventario
from src.infrastructure.db.models.papeleria import (
    CajaRegistradora,
    Estacion,
    Papeleria,
    Sucursal,
)
from src.infrastructure.db.models.usuario import (
    TUsuario,
    UsuarioPapeleriaRel,
    UsuarioSesion,
)
from src.infrastructure.db.models.venta import (
    OutboxEvento,
    TDetalleVenta,
    TDlqEvento,
    THistorialVentas,
    TPagoVenta,
    TVenta,
)

__all__ = [
    "Base",
    # Tenancy
    "Papeleria",
    "Sucursal",
    "CajaRegistradora",
    "Estacion",
    # Usuarios
    "TUsuario",
    "UsuarioPapeleriaRel",
    "UsuarioSesion",
    # Catálogo S2
    "TUnidadMedida",
    "TImpuesto",
    "TArticulo",
    # Inventario S2
    "TLote",
    "TMovInventario",
    # Ventas + Outbox + DLQ S3
    "TVenta",
    "TDetalleVenta",
    "TPagoVenta",
    "THistorialVentas",
    "OutboxEvento",
    "TDlqEvento",
]
