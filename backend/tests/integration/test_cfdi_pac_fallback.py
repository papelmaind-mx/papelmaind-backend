"""T10 cfdi_pac_fallback — PAC_PRIMARY caído → PAC_FALLBACK → timbrado exitoso.

Test unitario del patrón de conmutación (canon <testing> tests_criticos).
El worker completo (generación CFDI + outbox + DLQ) llega en Sprint 7;
la lógica de failover se valida YA con httpx MockTransport.
"""
from __future__ import annotations

import httpx
import pytest

from src.infrastructure.workers.cfdi_worker import PacClient, PacUnavailableError, timbrar_cfdi

pytestmark = pytest.mark.asyncio

CFDI_DEMO = {
    "serie": "A",
    "folio": "1",
    "emisor_rfc": "PMA260101XXX",
    "receptor_rfc": "XAXX010101000",
    "total": "413.00",
}


def _mock_handler(fail_primary: bool):
    calls: list[str] = []

    def _handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        calls.append(url)
        if "primary" in url and fail_primary:
            return httpx.Response(503, json={"error": "PAC saturado"})
        payload = {"uuid": "11111111-2222-3333-4444-555555555555", "xml": "<cfdi/>"}
        return httpx.Response(200, json=payload)

    return _handler, calls


class TestT10CfdiPacFallback:
    async def test_primary_caido_conmuta_a_fallback(self):
        handler, calls = _mock_handler(fail_primary=True)
        client = PacClient()
        transport = httpx.MockTransport(handler)
        client._try_pac = _patched_try(transport)  # type: ignore[method-assign]

        result = await timbrar_cfdi(CFDI_DEMO, client)
        assert result.pac == "fallback"
        assert result.uuid_timbrado == "11111111-2222-3333-4444-555555555555"
        assert result.xml == "<cfdi/>"
        # Hubo llamadas a ambos PACs
        assert any("primary" in c for c in calls), calls
        assert any("fallback" in c for c in calls), calls

    async def test_primary_sano_no_toca_fallback(self):
        handler, calls = _mock_handler(fail_primary=False)
        client = PacClient()
        client._try_pac = _patched_try(httpx.MockTransport(handler))  # type: ignore[method-assign]

        result = await timbrar_cfdi(CFDI_DEMO, client)
        assert result.pac == "primary"
        assert all("fallback" not in c for c in calls), calls

    async def test_ambos_caidos_levanta_pac_unavailable(self):
        def _all_down(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, json={"error": "down"})

        client = PacClient()
        client._try_pac = _patched_try(httpx.MockTransport(_all_down))  # type: ignore[method-assign]

        with pytest.raises(PacUnavailableError):
            await timbrar_cfdi(CFDI_DEMO, client)


def _patched_try(transport: httpx.MockTransport):
    """Reemplaza _try_pac con un cliente httpx mockeado (sin red).

    Nota: los atributos de instancia NO se enlazan como métodos,
    por eso la firma es (base_url, cfdi) sin self.
    """

    async def _try(base_url: str, cfdi: dict) -> dict:
        async with httpx.AsyncClient(transport=transport, timeout=5) as client:
            resp = await client.post(f"{base_url}/timbrado", json=cfdi)
            resp.raise_for_status()
            return resp.json()

    return _try
