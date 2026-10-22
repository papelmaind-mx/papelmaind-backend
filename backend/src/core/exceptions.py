"""Excepciones de dominio — canon CONV-05: HTTPException SOLO en capa API."""
from __future__ import annotations


class PapelMaindError(Exception):
    """Base de errores de dominio PapelMaind."""


class InsufficientStockError(PapelMaindError):
    """F20/FEFO: no hay stock suficiente para la venta."""

    def __init__(self, articulo_id: str, pendiente: str = "") -> None:
        self.articulo_id = articulo_id
        self.pendiente = pendiente
        super().__init__(f"Stock insuficiente para articulo {articulo_id} (pendiente {pendiente})")


class AuthenticationError(PapelMaindError):
    """Credenciales inválidas o token expirado/inválido."""


class TenantSelectionRequired(PapelMaindError):
    """Login multi-tenant: el usuario pertenece a varios tenants y no seleccionó uno."""

    def __init__(self, tenants: list[dict]) -> None:
        self.tenants = tenants
        super().__init__("Selección explícita de tenant requerida")


class ForbiddenError(PapelMaindError):
    """Rol insuficiente para el recurso."""


class NotFoundError(PapelMaindError):
    """Recurso inexistente en el tenant actual (RLS)."""


class DuplicateEntityError(PapelMaindError):
    """Violación de unicidad (ej. UNIQUE(papeleria_id, sku))."""


class PaymentError(PapelMaindError):
    """S3: pagos inconsistentes con el total de la venta (monto insuficiente/mixto sin desglose)."""
