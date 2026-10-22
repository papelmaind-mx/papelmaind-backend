"""Dependencias de BD — get_db (público) y get_tenant_db (RLS por tenant)."""
from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.db.session import get_session_factory, set_tenant_context


async def get_db() -> AsyncIterator[AsyncSession]:
    """Sesión plana (health, login, selección de tenants — sin contexto RLS)."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def get_tenant_db(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> AsyncIterator[AsyncSession]:
    """Sesión con contexto tenant fijado desde el JWT (RLS).

    En PostgreSQL aplica SET LOCAL app.current_tenant_id (RLS real);
    en SQLite registra session.info['tenant_id'] (RLS emulado — los endpoints
    SIEMPRE filtran por papeleria_id del usuario actual).
    """
    user = getattr(request.state, "current_user", None)
    if user is not None:
        await set_tenant_context(session, str(user.tenant_id))
    yield session
