"""Router /catalog — unidades de medida, impuestos y artículos (S2).

RLS: toda consulta filtra por papeleria_id del JWT (PG: RLS real; SQLite: emulado).
Roles canon: admin gestiona catálogo; cajero/inventariado consultan.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.auth import CurrentUser, require_roles
from src.api.dependencies.db import get_tenant_db
from src.core.exceptions import DuplicateEntityError, NotFoundError
from src.infrastructure.db.models import TArticulo, TImpuesto, TUnidadMedida
from src.schemas.catalog import (
    ArticuloCreate,
    ArticuloRead,
    ArticuloUpdate,
    ImpuestoCreate,
    ImpuestoRead,
    UnidadMedidaCreate,
    UnidadMedidaRead,
)

router = APIRouter(prefix="/catalog", tags=["catalog"])


def _tenant_filter(user: CurrentUser):
    """Filtro explícito por tenant — obligatorio en modo SQLite (RLS emulado)."""
    return TUnidadMedida.papeleria_id == user.tenant_id


# ==================== UNIDADES DE MEDIDA ====================
@router.post(
    "/unidades-medida",
    response_model=UnidadMedidaRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_unidad_medida(
    payload: UnidadMedidaCreate,
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
    current_user: Annotated[CurrentUser, Depends(require_roles("admin"))],
) -> UnidadMedidaRead:
    dup = (
        await db.execute(
            select(TUnidadMedida).where(
                TUnidadMedida.papeleria_id == current_user.tenant_id,
                TUnidadMedida.clave == payload.clave,
            )
        )
    ).scalar_one_or_none()
    if dup is not None:
        raise DuplicateEntityError(f"Unidad {payload.clave} ya existe en este tenant")
    unidad = TUnidadMedida(papeleria_id=current_user.tenant_id, **payload.model_dump())
    db.add(unidad)
    await db.commit()
    await db.refresh(unidad)
    return unidad


@router.get("/unidades-medida", response_model=list[UnidadMedidaRead])
async def list_unidades_medida(
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
    current_user: Annotated[CurrentUser, Depends(require_roles("admin", "cajero", "contador"))],
) -> list[UnidadMedidaRead]:
    result = await db.execute(
        select(TUnidadMedida)
        .where(TUnidadMedida.papeleria_id == current_user.tenant_id)
        .order_by(TUnidadMedida.clave)
    )
    return list(result.scalars().all())


# ==================== IMPUESTOS ====================
@router.post("/impuestos", response_model=ImpuestoRead, status_code=status.HTTP_201_CREATED)
async def create_impuesto(
    payload: ImpuestoCreate,
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
    current_user: Annotated[CurrentUser, Depends(require_roles("admin"))],
) -> ImpuestoRead:
    dup = (
        await db.execute(
            select(TImpuesto).where(
                TImpuesto.papeleria_id == current_user.tenant_id,
                TImpuesto.nombre == payload.nombre,
            )
        )
    ).scalar_one_or_none()
    if dup is not None:
        raise DuplicateEntityError(f"Impuesto {payload.nombre} ya existe en este tenant")
    impuesto = TImpuesto(papeleria_id=current_user.tenant_id, **payload.model_dump())
    db.add(impuesto)
    await db.commit()
    await db.refresh(impuesto)
    return impuesto


@router.get("/impuestos", response_model=list[ImpuestoRead])
async def list_impuestos(
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
    current_user: Annotated[CurrentUser, Depends(require_roles("admin", "cajero", "contador"))],
) -> list[ImpuestoRead]:
    result = await db.execute(
        select(TImpuesto).where(TImpuesto.papeleria_id == current_user.tenant_id)
    )
    return list(result.scalars().all())


# ==================== ARTÍCULOS ====================
@router.post("/articulos", response_model=ArticuloRead, status_code=status.HTTP_201_CREATED)
async def create_articulo(
    payload: ArticuloCreate,
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
    current_user: Annotated[CurrentUser, Depends(require_roles("admin"))],
) -> ArticuloRead:
    unidad = (
        await db.execute(
            select(TUnidadMedida).where(
                TUnidadMedida.id == payload.unidad_medida_id,
                TUnidadMedida.papeleria_id == current_user.tenant_id,
            )
        )
    ).scalar_one_or_none()
    if unidad is None:
        raise NotFoundError("Unidad de medida no encontrada en este tenant")

    dup = (
        await db.execute(
            select(TArticulo).where(
                TArticulo.papeleria_id == current_user.tenant_id,
                TArticulo.sku == payload.sku,
            )
        )
    ).scalar_one_or_none()
    if dup is not None:
        raise DuplicateEntityError(f"SKU {payload.sku} ya existe en este tenant")

    articulo = TArticulo(
        papeleria_id=current_user.tenant_id,
        **payload.model_dump(),
        stock_actual=Decimal("0.000"),
        stock_reservado=Decimal("0.000"),
    )
    db.add(articulo)
    await db.commit()
    await db.refresh(articulo)
    return articulo


@router.get("/articulos", response_model=list[ArticuloRead])
async def list_articulos(
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
    current_user: Annotated[CurrentUser, Depends(require_roles("admin", "cajero", "contador"))],
    q: str | None = None,
) -> list[ArticuloRead]:
    stmt = select(TArticulo).where(TArticulo.papeleria_id == current_user.tenant_id)
    if q:
        stmt = stmt.where(TArticulo.descripcion.ilike(f"%{q}%"))
    result = await db.execute(stmt.order_by(TArticulo.sku))
    return list(result.scalars().all())


@router.get("/articulos/{articulo_id}", response_model=ArticuloRead)
async def get_articulo(
    articulo_id: UUID,
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
    current_user: Annotated[CurrentUser, Depends(require_roles("admin", "cajero", "contador"))],
) -> ArticuloRead:
    # T5: el filtro por tenant hace que el id de OTRO tenant → 404
    articulo = (
        await db.execute(
            select(TArticulo).where(
                TArticulo.id == articulo_id,
                TArticulo.papeleria_id == current_user.tenant_id,
            )
        )
    ).scalar_one_or_none()
    if articulo is None:
        raise NotFoundError("Artículo no encontrado")
    return articulo


@router.patch("/articulos/{articulo_id}", response_model=ArticuloRead)
async def update_articulo(
    articulo_id: UUID,
    payload: ArticuloUpdate,
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
    current_user: Annotated[CurrentUser, Depends(require_roles("admin"))],
) -> ArticuloRead:
    articulo = (
        await db.execute(
            select(TArticulo).where(
                TArticulo.id == articulo_id,
                TArticulo.papeleria_id == current_user.tenant_id,
            )
        )
    ).scalar_one_or_none()
    if articulo is None:
        raise NotFoundError("Artículo no encontrado")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(articulo, field, value)
    await db.commit()
    await db.refresh(articulo)
    return articulo
