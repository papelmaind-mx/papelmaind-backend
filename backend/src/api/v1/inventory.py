"""Router /inventory — recepción de mercancía (lotes) y FEFO (S2).

POST /inventory/lotes: crea lote + tmovinventario 'entrada' + incrementa stock_actual.
POST /inventory/allocate: hard-allocate FEFO (canon: ÚNICO punto que consume lotes).
"""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.auth import CurrentUser, require_roles
from src.api.dependencies.db import get_tenant_db
from src.application.services.fefo_allocator import allocate_stock_fefo
from src.core.exceptions import InsufficientStockError, NotFoundError
from src.infrastructure.db.models import TArticulo, TLote, TMovInventario
from src.schemas.catalog import LoteCreate, LoteRead

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/lotes", response_model=LoteRead, status_code=status.HTTP_201_CREATED)
async def receive_lote(
    payload: LoteCreate,
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
    current_user: Annotated[CurrentUser, Depends(require_roles("admin", "cajero"))],
) -> LoteRead:
    """Recepción de mercancía: lote + movimiento 'entrada' + stock global."""
    articulo = (
        await db.execute(
            select(TArticulo).where(
                TArticulo.id == payload.articulo_id,
                TArticulo.papeleria_id == current_user.tenant_id,
            )
        )
    ).scalar_one_or_none()
    if articulo is None:
        raise NotFoundError("Artículo no encontrado en este tenant")

    nuevo_lote = TLote(
        papeleria_id=current_user.tenant_id,
        sucursal_id=payload.sucursal_id,
        articulo_id=payload.articulo_id,
        numero_lote=payload.numero_lote,
        fecha_vencimiento=payload.fecha_vencimiento,
        costo_unitario=payload.costo_unitario,
        cantidad_actual=payload.cantidad_actual,
        estado="disponible",
    )
    db.add(nuevo_lote)
    await db.flush()

    db.add(
        TMovInventario(
            papeleria_id=current_user.tenant_id,
            sucursal_id=payload.sucursal_id,
            articulo_id=articulo.id,
            lote_id=nuevo_lote.id,
            tipo_movimiento="entrada",
            cantidad=payload.cantidad_actual,
            motivo="Recepción de mercancía",
        )
    )
    articulo.stock_actual += payload.cantidad_actual
    await db.commit()
    await db.refresh(nuevo_lote)
    return nuevo_lote


@router.get("/lotes", response_model=list[LoteRead])
async def list_lotes(
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
    current_user: Annotated[CurrentUser, Depends(require_roles("admin", "cajero", "contador"))],
    articulo_id: UUID | None = None,
) -> list[LoteRead]:
    stmt = select(TLote).where(TLote.papeleria_id == current_user.tenant_id)
    if articulo_id is not None:
        stmt = stmt.where(TLote.articulo_id == articulo_id)
    result = await db.execute(stmt.order_by(TLote.fecha_vencimiento.asc()))
    return list(result.scalars().all())


class AllocateRequest(BaseModel):
    articulo_id: UUID
    cantidad: Decimal = Field(gt=0, max_digits=12, decimal_places=3)


class AllocateResponse(BaseModel):
    ok: bool = True
    articulo_id: UUID
    cantidad: Decimal
    stock_actual_restante: Decimal


@router.post("/allocate", response_model=AllocateResponse)
async def allocate_fefo(
    payload: AllocateRequest,
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
    current_user: Annotated[CurrentUser, Depends(require_roles("admin", "cajero"))],
) -> AllocateResponse:
    """Hard-allocate FEFO — consumo de lotes por vencimiento (uso interno POS S3)."""
    try:
        await allocate_stock_fefo(db, current_user.tenant_id, payload.articulo_id, payload.cantidad)
    except InsufficientStockError:
        raise
    await db.commit()
    articulo = (
        await db.execute(
            select(TArticulo).where(
                TArticulo.id == payload.articulo_id,
                TArticulo.papeleria_id == current_user.tenant_id,
            )
        )
    ).scalar_one()
    return AllocateResponse(
        articulo_id=payload.articulo_id,
        cantidad=payload.cantidad,
        stock_actual_restante=articulo.stock_actual,
    )
