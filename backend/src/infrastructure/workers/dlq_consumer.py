"""DLQ Consumer — eventos terminales con reintento y audit DLQ_* (S3).

Ciclo de vida del DLQ (canon tdlq_eventos):
  pendiente → (admin marca) reintentado → run_once reintenta el handler:
    · éxito  → estado='resuelto' + outbox.procesado_loyalty=true
    · fallo  → estado='reintentado' + historial_intentos.append(error)
  pendiente → (admin) descartado (motivo + descartado_por, audit DLQ_DISCARD)

Los 6 endpoints admin (/admin/dlq) se exponen en el router de administración;
este módulo concentra la lógica de reintento reutilizable.
"""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError, PapelMaindError
from src.core.logging import logger
from src.core.metrics import inc_counter
from src.infrastructure.db.models import OutboxEvento, TDlqEvento
from src.infrastructure.workers.loyalty_worker import _handle_sale_completed


def _as_uuid(value: str | UUID) -> UUID:
    return value if isinstance(value, UUID) else UUID(str(value))


async def retry_dlq_event(session: AsyncSession, dlq_id: str | UUID) -> TDlqEvento:
    """Reintenta UN evento del DLQ (endpoint admin + ciclo automático).

    Solo filas en 'pendiente' o 'reintentado'. Éxito → resuelto + checkpoint
    del outbox; fallo de dominio → reintentado + historial ampliado.
    """
    dlq = await session.get(TDlqEvento, _as_uuid(dlq_id))
    if dlq is None:
        raise NotFoundError("Evento DLQ no encontrado")
    if dlq.estado not in ("pendiente", "reintentado"):
        raise PapelMaindError(f"Evento DLQ en estado terminal '{dlq.estado}'")

    evento = await session.get(OutboxEvento, dlq.outbox_evento_id)
    try:
        if evento is None:
            raise PapelMaindError("outbox_evento huérfano")
        await _handle_sale_completed(session, evento)
    except PapelMaindError as error:
        historial = list(dlq.historial_intentos or [])
        historial.append(
            {"ts": datetime.now(UTC).isoformat(), "error": str(error)[:200]}
        )
        dlq.historial_intentos = historial
        dlq.error_ultimo = str(error)[:500]
        dlq.estado = "reintentado"
        logger.warning("dlq_retry_failed", dlq=dlq.id, error=str(error))
        return dlq

    dlq.estado = "resuelto"
    evento.procesado_loyalty = True
    evento.procesado_en = datetime.now(UTC)
    inc_counter("erp_dlq_resolved_total")
    logger.info("dlq_event_resolved", dlq=dlq.id, evento=evento.id)
    return dlq


async def discard_dlq_event(
    session: AsyncSession, dlq_id: str | UUID, *, motivo: str, usuario_id: str | UUID
) -> TDlqEvento:
    """Descarte manual auditable (accion DLQ_DISCARD en tauditlogs vía capa API)."""
    dlq = await session.get(TDlqEvento, _as_uuid(dlq_id))
    if dlq is None:
        raise NotFoundError("Evento DLQ no encontrado")
    if dlq.estado in ("descartado", "resuelto"):
        raise PapelMaindError(f"Evento DLQ ya terminal ('{dlq.estado}')")
    dlq.estado = "descartado"
    dlq.motivo_descarte = motivo
    dlq.descartado_por = _as_uuid(usuario_id)
    dlq.descartado_en = datetime.now(UTC)
    return dlq


async def run_once(session: AsyncSession) -> dict:
    """Reintenta los eventos marcados 'reintentado' (política admin)."""
    reintentados = (
        (
            await session.execute(
                select(TDlqEvento).where(TDlqEvento.estado == "reintentado")
            )
        )
        .scalars()
        .all()
    )
    resueltos = 0
    fallidos = 0
    for dlq in reintentados:
        resultado = await retry_dlq_event(session, dlq.id)
        if resultado.estado == "resuelto":
            resueltos += 1
        else:
            fallidos += 1
    return {"resueltos": resueltos, "fallidos": fallidos}
