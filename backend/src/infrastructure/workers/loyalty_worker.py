"""Loyalty Worker — F17: consumidor con flag propio procesado_loyalty.

Polling P0 (idx_outbox_loyalty_p0): eventos sale.completed pendientes.
- Éxito → procesado_loyalty=true + procesado_en (checkpoint EXCLUSIVO aquí).
- Error de DOMINIO (payload inválido, regla rota) → TDlqEvento terminal
  (ON CONFLICT DO NOTHING por outbox_evento_id) + métrica erp_outbox_dlq_total.
- Error transitorio (infra) → sin marca: se reintenta en el siguiente ciclo
  (consumers idempotentes por diseño, canon F17).

La acumulación de puntos (S5-S6) vive en _handle_sale_completed; en S3 el
handler valida el contrato del payload — suficiente para ejercitar el DLQ.
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.core.exceptions import PapelMaindError
from src.core.logging import logger
from src.core.metrics import inc_counter
from src.infrastructure.db.models import OutboxEvento, TDlqEvento

BATCH_SIZE = 50


def validate_sale_completed_payload(payload: dict) -> None:
    """Contrato del evento sale.completed (S3). Falla → error de dominio → DLQ."""
    if not isinstance(payload, dict):
        raise PapelMaindError("sale.completed: payload no es objeto")
    for campo in ("venta_id", "folio", "total", "items"):
        if campo not in payload:
            raise PapelMaindError(f"sale.completed: falta campo '{campo}'")
    try:
        Decimal(str(payload["total"]))
    except (InvalidOperation, ValueError) as exc:
        raise PapelMaindError(f"sale.completed: total no numérico ({payload['total']!r})") from exc
    if not isinstance(payload["items"], list) or not payload["items"]:
        raise PapelMaindError("sale.completed: items vacío o inválido")


async def _handle_sale_completed(session: AsyncSession, evento: OutboxEvento) -> None:
    """Dominio del evento. S5+: acumulación de puntos ttarjetaconsentido."""
    validate_sale_completed_payload(evento.payload)


async def _to_dlq(session: AsyncSession, evento: OutboxEvento, error: PapelMaindError) -> None:
    """Error de dominio → DLQ terminal (idempotente por outbox_evento_id)."""
    session.add(
        TDlqEvento(
            outbox_evento_id=evento.id,
            papeleria_id=evento.papeleria_id,
            event_type=evento.tipo,
            aggregate_type=evento.aggregate_type,
            aggregate_id=evento.aggregate_id,
            payload=evento.payload,
            error_ultimo=str(error)[:500],
            historial_intentos=[
                {"ts": datetime.now(UTC).isoformat(), "error": str(error)[:200]}
            ],
            estado="pendiente",
        )
    )
    inc_counter("erp_outbox_dlq_total")


async def pending_sale_events(session: AsyncSession) -> list[OutboxEvento]:
    """Eventos sale.completed pendientes NO castigados al DLQ (idx_outbox_loyalty_p0)."""
    en_dlq = select(TDlqEvento.outbox_evento_id).where(
        TDlqEvento.outbox_evento_id == OutboxEvento.id
    )
    return list(
        (
            await session.execute(
                select(OutboxEvento)
                .where(
                    OutboxEvento.tipo == "sale.completed",
                    OutboxEvento.procesado_loyalty.is_(False),
                    ~en_dlq.exists(),
                )
                .order_by(OutboxEvento.created_at.asc())
                .limit(BATCH_SIZE)
            )
        )
        .scalars()
        .all()
    )


async def run_once(session: AsyncSession) -> dict:
    """Un ciclo: procesa lote de eventos. Retorna estadísticas del ciclo."""
    procesados = 0
    a_dlq = 0
    for evento in await pending_sale_events(session):
        try:
            await _handle_sale_completed(session, evento)
        except PapelMaindError as domain_error:
            await _to_dlq(session, evento, domain_error)
            a_dlq += 1
            logger.warning(
                "outbox_event_to_dlq", evento=evento.id, error=str(domain_error)
            )
        else:
            evento.procesado_loyalty = True
            evento.procesado_en = datetime.now(UTC)
            procesados += 1
    return {"procesados": procesados, "a_dlq": a_dlq}


async def run() -> None:
    """Loop perpetuo del loyalty worker (polling P0)."""
    from src.infrastructure.db.session import get_session_factory

    factory: async_sessionmaker[AsyncSession] = get_session_factory()
    logger.info("loyalty_worker_started", modo="polling-p0")
    while True:
        try:
            async with factory() as session:
                stats = await run_once(session)
                await session.commit()
            if stats["procesados"] or stats["a_dlq"]:
                logger.info("loyalty_worker_cycle", **stats)
        except Exception:  # noqa: BLE001 — el worker jamás muere
            logger.exception("loyalty_worker_cycle_failed")
        await asyncio.sleep(2.0)
