"""FEFOAllocator — canon Sección <servicios_core> (código canon, adaptado a tipos).

Hard-allocate FEFO: consume lotes por fecha de vencimiento ascendente.
F20: este es el ÚNICO punto que consume lotes (la reserva de carrito es
candado blando a nivel artículo). Registra tmovinventario tipo 'salida'.
"""
from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import InsufficientStockError
from src.core.metrics import monitor_latency
from src.infrastructure.db.models import TArticulo, TLote, TMovInventario


@monitor_latency("erp_fefo_allocation_latency_seconds")
async def _allocate(
    session: AsyncSession, tenant_id: UUID, articulo_id: UUID, cantidad: Decimal
) -> list[tuple[UUID, Decimal]]:
    """Consume lotes FEFO. Retorna [(lote_id, cantidad_consumida), ...] para trazabilidad."""
    art = (
        await session.execute(
            select(TArticulo).where(
                TArticulo.id == articulo_id, TArticulo.papeleria_id == tenant_id
            ).with_for_update()
        )
    ).scalar_one_or_none()
    if not art or (art.stock_actual - art.stock_reservado) < cantidad:
        raise InsufficientStockError(str(articulo_id))

    lotes = (
        (
            await session.execute(
                select(TLote)
                .where(
                    TLote.papeleria_id == tenant_id,
                    TLote.articulo_id == articulo_id,
                    TLote.estado.in_(("disponible", "parcial")),
                )
                .order_by(TLote.fecha_vencimiento.asc())
                .with_for_update()
            )
        )
        .scalars()
        .all()
    )

    consumidos: list[tuple[UUID, Decimal]] = []
    pendiente = cantidad
    for lote in lotes:
        if pendiente <= 0:
            break
        disponible = lote.cantidad_actual - lote.cantidad_reservada
        if disponible <= 0:
            continue
        take = min(disponible, pendiente)
        lote.cantidad_actual -= take
        if lote.cantidad_actual == 0:
            lote.estado = "agotado"
        elif lote.estado == "disponible":
            lote.estado = "parcial"
        session.add(
            TMovInventario(
                papeleria_id=tenant_id,
                articulo_id=articulo_id,
                lote_id=lote.id,
                tipo_movimiento="salida",
                cantidad=take,
                motivo="Venta",
            )
        )
        consumidos.append((lote.id, take))
        pendiente -= take

    if pendiente > 0:
        raise InsufficientStockError(str(articulo_id), pendiente=str(pendiente))

    art.stock_actual -= cantidad
    art.stock_reservado = max(Decimal("0"), art.stock_reservado - cantidad)
    return consumidos


async def allocate_stock_fefo(
    session: AsyncSession, tenant_id: UUID, articulo_id: UUID, cantidad: Decimal
) -> list[tuple[UUID, Decimal]]:
    """Asigna `cantidad` consumiendo lotes FEFO dentro de la TX abierta.

    Retorna los lotes consumidos [(lote_id, take)] — el detalle de venta fija
    el primer lote (vencimiento más cercano) como referencia de trazabilidad.
    """
    return await _allocate(session, tenant_id, articulo_id, cantidad)
