"""Routers S3+ — stubs declarativos (CHK-01: rutas completas resuelven).

Cada módulo se implementa en su sprint correspondiente (roadmap canon):
S3-3.5: pos, sync offline · S4: cash, aparados · S5-6: loyalty/campanas
S7: fiscal/autofactura · S8: ecommerce, webhooks, shipping · Kiosco S4.5
"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()

_STUBS: list[tuple[str, str, int]] = [
    ("/pos/sync", "Sincronización offline-first POS (Sprint 3.5)", 501),
    ("/cash/cortes", "Apertura/cierre de caja y movimientos (Sprint 4)", 501),
    ("/aparados", "Apartados con abonos + hard-allocate FEFO al liquidar (Sprint 4)", 501),
    ("/ecommerce/carritos", "Carrito con reserva blanda TTL 15min (Sprint 8)", 501),
    ("/webhooks/payments", "Webhook MercadoPago idempotente (Sprint 8)", 501),
    ("/autofactura/solicitar", "Token autofactura CFDI 4.0 (Sprint 7)", 501),
    ("/whatsapp/webhook", "WhatsApp Cloud API con resolve_tenant_context (Sprint 5-6)", 501),
    ("/shipping/tracking", "Logística local y tracking QR (Sprint 8)", 501),
    ("/kiosco/ventas", "Venta autoservicio + outbox (Sprint 4.5)", 501),
    ("/campanas", "Campañas CRM con IA (Sprint 6)", 501),
    ("/contabilidad", "Reportes contables/fiscales (Sprint 7)", 501),
    ("/admin/dlq/eventos", "6 endpoints admin DLQ (Sprint 3)", 501),
]


def _build_stub_router() -> APIRouter:
    stub = APIRouter(tags=["stubs"])
    for path, desc, code in _STUBS:
        @stub.get(path, summary=desc, include_in_schema=True)  # type: ignore[misc]
        async def _stub(desc: str = desc, code: int = code) -> dict:  # noqa: B008
            return {"detail": desc, "status_code": code, "sprint": "pendiente"}
    return stub


stub_router = _build_stub_router()
