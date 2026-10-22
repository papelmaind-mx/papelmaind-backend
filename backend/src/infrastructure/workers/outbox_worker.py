"""Outbox Worker — F17: P0-aware con flags SEPARADOS por consumidor.

P0 (sin Kafka): el worker SOLO mantiene la métrica de backlog
`erp_outbox_pending_events_count` (alerta A1 OutboxLagging). El flag
`publicado_kafka` permanece false para siempre en P0 — checkpoint exclusivo
de este worker (canon F17), NO un 'procesado' global.

P1 (Kafka KRaft): polling con FOR UPDATE SKIP LOCKED + publicación JSON Schema
+ publicado_kafka=true + intentos<3 (idx_outbox_kafka_p1).
"""
from __future__ import annotations

import asyncio

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.core.config import settings
from src.core.logging import logger
from src.core.metrics import set_gauge
from src.infrastructure.db.models import OutboxEvento

POLL_INTERVAL = getattr(settings, "outbox_poll_interval_s", 5.0)


async def update_pending_gauge(session: AsyncSession) -> int:
    """Gauge de backlog pendiente (A1 OutboxLagging: >100 por 3m = critical)."""
    pendientes = (
        await session.execute(
            select(func.count())
            .select_from(OutboxEvento)
            .where(
                OutboxEvento.tipo == "sale.completed",
                OutboxEvento.procesado_loyalty.is_(False),
            )
        )
    ).scalar_one()
    set_gauge("erp_outbox_pending_events_count", float(pendientes))
    return int(pendientes)


async def run_once(session_factory: async_sessionmaker[AsyncSession]) -> dict:
    """Un ciclo del worker: métrica de backlog (P0)."""
    async with session_factory() as session:
        pendientes = await update_pending_gauge(session)
        await session.commit()
    if pendientes:
        logger.info("outbox_backlog", pendientes=pendientes)
    return {"pendientes": pendientes}


async def run() -> None:
    """Loop perpetuo del outbox worker (P0: gauge; P1: publish a Kafka)."""
    from src.infrastructure.db.session import get_session_factory

    factory = get_session_factory()
    logger.info("outbox_worker_started", mode="P0-gauge-only")
    while True:
        try:
            await run_once(factory)
        except Exception:  # noqa: BLE001 — el worker jamás muere
            logger.exception("outbox_worker_cycle_failed")
        await asyncio.sleep(POLL_INTERVAL)
