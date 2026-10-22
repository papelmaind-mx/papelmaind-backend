"""PacClient — CFDI 4.0 timbrado con PAC primario + fallback (T10 cfdi_pac_fallback).

Patrón canon (Sección facturación): PAC_PRIMARY caído → PAC_FALLBACK → timbrado
exitoso. Se implementa el cliente con reintentos (tenacity) y fallback explícito;
el worker completo (S7) orquestará generación de CFDI + outbox + DLQ.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.core.config import settings
from src.core.logging import logger


class PacUnavailableError(Exception):
    """Ambos PACs (primario y fallback) fallaron."""


@dataclass(frozen=True)
class PacResult:
    pac: str
    uuid_timbrado: str
    xml: str


class PacClient:
    """Cliente de timbrado con conmutación automática PAC_PRIMARY → PAC_FALLBACK."""

    def __init__(self) -> None:
        self.primary_url = settings.pac_primary_url
        self.fallback_url = settings.pac_fallback_url
        self.timeout = settings.pac_timeout_seconds

    @retry(
        retry=retry_if_exception_type((httpx.HTTPError, httpx.HTTPStatusError)),
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=0.2, min=0.2, max=1),
        reraise=True,
    )
    async def _try_pac(self, base_url: str, cfdi: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(f"{base_url}/timbrado", json=cfdi)
            resp.raise_for_status()
            return resp.json()

    async def timbrar(self, cfdi: dict[str, Any]) -> PacResult:
        """Intenta PAC primario; si cae, conmuta al fallback (T10)."""
        try:
            data = await self._try_pac(self.primary_url, cfdi)
            logger.info("cfdi_timbrado", pac="primary")
            return PacResult(pac="primary", uuid_timbrado=data["uuid"], xml=data["xml"])
        except Exception as primary_err:
            logger.warning("pac_primary_down", error=str(primary_err))
            try:
                data = await self._try_pac(self.fallback_url, cfdi)
                logger.info("cfdi_timbrado", pac="fallback")
                return PacResult(pac="fallback", uuid_timbrado=data["uuid"], xml=data["xml"])
            except Exception as fallback_err:
                raise PacUnavailableError(
                    f"primary={primary_err!r} fallback={fallback_err!r}"
                ) from fallback_err


async def timbrar_cfdi(cfdi: dict[str, Any], client: PacClient | None = None) -> PacResult:
    """Función usada por cfdi_worker (S7). Inyectable para tests (T10)."""
    pac = client or PacClient()
    return await pac.timbrar(cfdi)
