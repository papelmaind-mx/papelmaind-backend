"""Router /tenants — tenants accesibles para el usuario autenticado."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.auth import CurrentUser, get_current_user
from src.api.dependencies.db import get_db
from src.infrastructure.db.models import Papeleria, UsuarioPapeleriaRel
from src.schemas.auth import TenantInfo

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.get("/mine", response_model=list[TenantInfo], summary="Mis papelerías (tenants)")
async def my_tenants(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> list[TenantInfo]:
    rows = (
        await db.execute(
            select(UsuarioPapeleriaRel, Papeleria)
            .join(Papeleria, Papeleria.id == UsuarioPapeleriaRel.papeleria_id)
            .where(UsuarioPapeleriaRel.usuario_id == current_user.user_id)
        )
    ).all()
    return [
        TenantInfo(
            papeleria_id=rel.papeleria_id, nombre=p.nombre, slug=p.slug, rol=rel.rol
        )
        for rel, p in rows
    ]
