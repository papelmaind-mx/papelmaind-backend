"""T11 whatsapp_webhook tenant isolation — F19 (canon estructura tests).

Requiere WhatsApp Cloud API + resolve_tenant_context (Sprint 5).
Se activa cuando el router /whatsapp/webhook esté implementado.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.skip(reason="Sprint 5 — WhatsApp Cloud API")]


async def test_webhook_tenant_isolation_placeholder() -> None:
    """F19: dos tenants con wa_business distintos no se filtran mensajes."""
    assert True
