"""SaleService — S3 POS transaccional.

Flujo ACID en UNA transacción (CONV-06):
  1. Reclama el client_uuid: INSERT ... ON CONFLICT DO NOTHING (CONV-13).
     Si ya existía → retorna la venta previa (replay idempotente, sin efectos).
  2. Hard-allocate FEFO por partida (único punto que consume lotes, F20).
  3. Detalles + pagos + historial.
  4. Encola outbox 'sale.completed' en la MISMA TX (F17).
Si cualquier paso falla, TODO revierte — incluida la reclamación del client_uuid,
por lo que el POS puede reintentar el mismo client_uuid cuando haya stock.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.fefo_allocator import allocate_stock_fefo
from src.application.services.outbox_service import enqueue_event
from src.core.exceptions import NotFoundError, PaymentError
from src.core.metrics import inc_counter
from src.core.security import uuid_v7
from src.infrastructure.db.models import (
    TArticulo,
    TDetalleVenta,
    THistorialVentas,
    TImpuesto,
    TPagoVenta,
    TVenta,
)
from src.schemas.sale import PagoIn, SaleCreate

_CENT = Decimal("0.01")


def _q2(value: Decimal) -> Decimal:
    return value.quantize(_CENT, rounding=ROUND_HALF_UP)


@dataclass
class SaleResult:
    venta: TVenta
    replayed: bool


async def _existing_sale(
    session: AsyncSession, tenant_id: UUID, client_uuid: UUID
) -> TVenta:
    venta = (
        await session.execute(
            select(TVenta).where(
                TVenta.client_uuid == client_uuid,
                TVenta.papeleria_id == tenant_id,
            )
        )
    ).scalar_one_or_none()
    if venta is None:
        # Colisión cross-tenant del UUID (imposible con v7): sin replay seguro
        raise NotFoundError("client_uuid ya registrado en otro tenant")
    return venta


async def _folio_siguiente(session: AsyncSession, tenant_id: UUID) -> str:
    total = (
        await session.execute(
            select(func.count()).select_from(TVenta).where(TVenta.papeleria_id == tenant_id)
        )
    ).scalar_one()
    return f"V-{int(total) + 1:06d}"


async def create_sale(
    session: AsyncSession, *, tenant_id: UUID, payload: SaleCreate
) -> SaleResult:
    """Crea una venta POS transaccional idempotente. NO hace commit (capa API decide)."""
    venta_id = uuid_v7()

    # ---------- 1. Reclamar client_uuid (CONV-13: ON CONFLICT DO NOTHING en BD) ----------
    dialect = session.bind.dialect.name if session.bind else "sqlite"
    values = {
        "id": venta_id,
        "papeleria_id": tenant_id,
        "sucursal_id": payload.sucursal_id,
        "estacion_id": payload.estacion_id,
        "cliente_rel_id": payload.cliente_rel_id,
        "corte_id": payload.corte_id,
        "folio": await _folio_siguiente(session, tenant_id),
        "client_uuid": payload.client_uuid,
        "subtotal": Decimal("0.00"),
        "impuestos": Decimal("0.00"),
        "total": Decimal("0.00"),
        "metodo_pago": payload.metodo_pago,
        "estado": "completada",
        "origen": payload.origen,
    }
    if dialect == "postgresql":
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        stmt = pg_insert(TVenta).values(**values).on_conflict_do_nothing(
            index_elements=["client_uuid"]
        )
    else:
        from sqlalchemy.dialects.sqlite import insert as sqlite_insert

        stmt = sqlite_insert(TVenta).values(**values).on_conflict_do_nothing(
            index_elements=["client_uuid"]
        )
    result = await session.execute(stmt)
    if result.rowcount == 0:
        # Replay idempotente: la venta ya existe — sin efectos secundarios duplicados
        venta = await _existing_sale(session, tenant_id, payload.client_uuid)
        return SaleResult(venta=venta, replayed=True)

    venta = await session.get(TVenta, venta_id)
    assert venta is not None  # insertado en esta TX

    # ---------- 2. Resolver catálogo (tenant-scoped) y calcular totales ----------
    articulo_ids = [line.articulo_id for line in payload.items]
    rows = (
        (
            await session.execute(
                select(TArticulo, TImpuesto)
                .join(TImpuesto, TArticulo.impuesto_id == TImpuesto.id, isouter=True)
                .where(
                    TArticulo.id.in_(articulo_ids),
                    TArticulo.papeleria_id == tenant_id,
                )
            )
        )
        .unique()
        .all()
    )
    por_articulo = {art.id: (art, imp) for art, imp in rows}
    if len(por_articulo) != len(set(articulo_ids)):
        faltantes = set(articulo_ids) - set(por_articulo)
        raise NotFoundError(f"Artículos no encontrados en este tenant: {faltantes}")

    subtotal_total = Decimal("0.00")
    impuestos_total = Decimal("0.00")

    for line in payload.items:
        art, imp = por_articulo[line.articulo_id]
        precio = line.precio_unitario or art.precio_base
        precio = _q2(precio)
        linea_subtotal = _q2(precio * line.cantidad)
        tasa = imp.tasa if imp is not None else Decimal("0")
        linea_impuesto = _q2(linea_subtotal * tasa)
        subtotal_total += linea_subtotal
        impuestos_total += linea_impuesto

        # Hard-allocate FEFO dentro de la MISMA TX (F20: único consumidor de lotes)
        consumidos = await allocate_stock_fefo(
            session, tenant_id, line.articulo_id, line.cantidad
        )
        session.add(
            TDetalleVenta(
                papeleria_id=tenant_id,
                venta_id=venta_id,
                articulo_id=line.articulo_id,
                lote_id=consumidos[0][0] if consumidos else None,
                cantidad=line.cantidad,
                precio_unitario=precio,
                subtotal=linea_subtotal,
                impuesto_id=art.impuesto_id,
            )
        )

    total = _q2(subtotal_total + impuestos_total)
    venta.subtotal = _q2(subtotal_total)
    venta.impuestos = _q2(impuestos_total)
    venta.total = total

    # ---------- 3. Pagos ----------
    pagos = payload.pagos
    if not pagos:
        if payload.metodo_pago == "mixto":
            raise PaymentError("Pago mixto requiere desglose de pagos")
        # Pago único implícito (spei se registra como transferencia en tpagosventa)
        tipo_pago = (
            "transferencia" if payload.metodo_pago == "spei" else payload.metodo_pago
        )
        pagos = (
            [PagoIn(tipo=tipo_pago, monto=total)]  # type: ignore[arg-type]
            if tipo_pago in ("efectivo", "tarjeta", "transferencia", "puntos", "credito")
            else []
        )
    if pagos and sum(p.monto for p in pagos) < total:
        raise PaymentError(f"Pagos insuficientes: suman menos que el total {total}")
    for pago in pagos:
        session.add(
            TPagoVenta(
                papeleria_id=tenant_id,
                venta_id=venta_id,
                tipo=pago.tipo,
                monto=_q2(pago.monto),
            )
        )

    # ---------- 4. Historial + Outbox (misma TX, CONV-06/F17) ----------
    session.add(
        THistorialVentas(
            venta_id=venta_id,
            estado_anterior=None,
            estado_nuevo="completada",
            motivo="Venta POS",
        )
    )
    await enqueue_event(
        session,
        tenant_id=tenant_id,
        event_type="sale.completed",
        aggregate_type="sale",
        aggregate_id=str(venta_id),
        client_uuid=payload.client_uuid,
        payload={
            "venta_id": str(venta_id),
            "folio": venta.folio,
            "total": str(total),
            "subtotal": str(venta.subtotal),
            "impuestos": str(venta.impuestos),
            "metodo_pago": payload.metodo_pago,
            "origen": payload.origen,
            "cliente_rel_id": str(payload.cliente_rel_id) if payload.cliente_rel_id else None,
            "items": [
                {
                    "articulo_id": str(line.articulo_id),
                    "cantidad": str(line.cantidad),
                    "precio_unitario": str(por_articulo[line.articulo_id][0].precio_base),
                }
                for line in payload.items
            ],
        },
    )
    inc_counter("erp_sales_total", {"origen": payload.origen})
    return SaleResult(venta=venta, replayed=False)
