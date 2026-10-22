"""Router /pos — S3: venta transaccional + outbox (T1 idempotencia, T3/T4 concurrencia).

POST /pos/ventas: idempotente por client_uuid (CONV-12/13). El replay retorna
la venta original (200) en lugar de crear una duplicada; primera creación → 201.
"""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.auth import CurrentUser, require_roles
from src.api.dependencies.db import get_tenant_db
from src.application.services.sale_service import create_sale
from src.core.exceptions import NotFoundError
from src.infrastructure.db.models import TDetalleVenta, TPagoVenta, TVenta
from src.schemas.sale import SaleCreate, SaleLineOut, SaleOut

router = APIRouter(prefix="/pos", tags=["pos"])


async def _load_sale(
    session: AsyncSession, tenant_id: UUID, venta_id: UUID
) -> tuple[TVenta, list[TDetalleVenta], list[TPagoVenta]]:
    venta = (
        await session.execute(
            select(TVenta).where(
                TVenta.id == venta_id, TVenta.papeleria_id == tenant_id
            )
        )
    ).scalar_one_or_none()
    if venta is None:
        raise NotFoundError("Venta no encontrada en este tenant")
    detalles = (
        (
            await session.execute(
                select(TDetalleVenta).where(TDetalleVenta.venta_id == venta_id)
            )
        )
        .scalars()
        .all()
    )
    pagos = (
        (
            await session.execute(select(TPagoVenta).where(TPagoVenta.venta_id == venta_id))
        )
        .scalars()
        .all()
    )
    return venta, list(detalles), list(pagos)


def _to_out(
    venta: TVenta,
    detalles: list[TDetalleVenta],
    pagos: list[TPagoVenta],
    replayed: bool = False,
) -> SaleOut:
    return SaleOut(
        id=venta.id,
        folio=venta.folio,
        client_uuid=venta.client_uuid,
        subtotal=venta.subtotal,
        impuestos=venta.impuestos,
        total=venta.total,
        metodo_pago=venta.metodo_pago,
        estado=venta.estado,
        origen=venta.origen,
        created_at=venta.created_at,
        items=[
            SaleLineOut(
                articulo_id=d.articulo_id,
                lote_id=d.lote_id,
                cantidad=d.cantidad,
                precio_unitario=d.precio_unitario,
                subtotal=d.subtotal,
                impuesto_id=d.impuesto_id,
            )
            for d in detalles
        ],
        pagos=[{"tipo": p.tipo, "monto": p.monto} for p in pagos],
        replayed=replayed,
    )


@router.post(
    "/ventas",
    response_model=SaleOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear venta POS (idempotente por client_uuid)",
)
async def create_pos_sale(
    payload: SaleCreate,
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
    current_user: Annotated[CurrentUser, Depends(require_roles("admin", "cajero"))],
    response: Response,
) -> SaleOut:
    """Venta transaccional: FEFO + pagos + outbox sale.completed en una sola TX ACID.

    Replay del mismo client_uuid → 200 con la venta original (sin duplicar efectos).
    """
    result = await create_sale(db, tenant_id=current_user.tenant_id, payload=payload)
    await db.commit()
    venta, detalles, pagos = await _load_sale(db, current_user.tenant_id, result.venta.id)
    if result.replayed:
        response.status_code = status.HTTP_200_OK
    return _to_out(venta, detalles, pagos, replayed=result.replayed)


@router.get("/ventas/{venta_id}", response_model=SaleOut, summary="Consultar venta por id")
async def get_sale(
    venta_id: UUID,
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
    current_user: Annotated[CurrentUser, Depends(require_roles("admin", "cajero", "contador"))],
) -> SaleOut:
    venta, detalles, pagos = await _load_sale(db, current_user.tenant_id, venta_id)
    return _to_out(venta, detalles, pagos)


@router.get("/ventas", response_model=list[SaleOut], summary="Listar ventas del tenant")
async def list_sales(
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
    current_user: Annotated[CurrentUser, Depends(require_roles("admin", "cajero", "contador"))],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[SaleOut]:
    ventas = (
        (
            await db.execute(
                select(TVenta)
                .where(TVenta.papeleria_id == current_user.tenant_id)
                .order_by(TVenta.created_at.desc())
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )
    out: list[SaleOut] = []
    for venta in ventas:
        detalles = (
            (
                await db.execute(
                    select(TDetalleVenta).where(TDetalleVenta.venta_id == venta.id)
                )
            )
            .scalars()
            .all()
        )
        pagos = (
            (
                await db.execute(select(TPagoVenta).where(TPagoVenta.venta_id == venta.id))
            )
            .scalars()
            .all()
        )
        out.append(_to_out(venta, list(detalles), list(pagos)))
    return out
