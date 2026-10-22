"""OutboxService — canon <servicios_core> fix F17 (código canon).

CONV-06: el outbox SIEMPRE se encola desde aplicación DENTRO de la misma
transacción ACID del agregado (NUNCA trigger de BD).
F17: flags separados por consumidor (publicado_kafka, procesado_loyalty).
"""
from __future__ import annotations

from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.db.models import OutboxEvento


async def enqueue_event(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    event_type: str,
    aggregate_type: str,
    aggregate_id: str,
    payload: dict,
    client_uuid: UUID | None = None,
) -> None:
    """Encola un evento en la MISMA TX del agregado (jamás commit aquí)."""
    safe_payload = jsonable_encoder(payload)
    session.add(
        OutboxEvento(
            papeleria_id=tenant_id,
            tipo=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=str(aggregate_id),
            payload=safe_payload,
            client_uuid=client_uuid,
            publicado_kafka=False,
            procesado_loyalty=False,
        )
    )
