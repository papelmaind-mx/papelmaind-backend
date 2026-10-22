"""Sesiones de BD — canon CONV-07: api_engine + worker_engine DUALES.

- api_engine: tráfico autenticado (RLS / filtros por tenant)
- worker_engine: SOLO para 9 workers + 4 endpoints públicos (BYPASSRLS en PG)

Dev sin Docker: SQLite/aiosqlite con RLS emulado en capa aplicación
(TenantUnitOfWork inyecta filtros papeleria_id).
Prod Docker: PostgreSQL 16 con RLS real vía SET LOCAL app.current_tenant_id.
"""
from __future__ import annotations

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import settings
from src.core.logging import logger

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None

# SQLite: habilitar FK enforcement (comportamiento PG por defecto)
_ENABLE_FK = "PRAGMA foreign_keys=ON"


def get_api_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)
        if settings.is_sqlite:

            @event.listens_for(_engine.sync_engine, "connect")
            def _fk_on(dbapi_conn, _record) -> None:  # pragma: no cover
                cursor = dbapi_conn.cursor()
                cursor.execute(_ENABLE_FK)
                cursor.close()

    return _engine


def get_worker_engine() -> AsyncEngine:
    """Worker engine — en PG usa rol erp_worker (BYPASSRLS); en SQLite es el mismo motor."""
    return get_api_engine()


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_api_engine(), expire_on_commit=False, class_=AsyncSession
        )
    return _session_factory


async def set_tenant_context(session: AsyncSession, tenant_id: str) -> None:
    """Fija el contexto de tenant para la transacción en curso.

    - PostgreSQL: SET LOCAL app.current_tenant_id (RLS real, transaccional)
    - SQLite (dev/test): registra el tenant en session.info → el TenantUnitOfWork
      y los repositorios aplican el filtro papeleria_id (RLS emulado).
    """
    session.info["tenant_id"] = tenant_id
    if not settings.is_sqlite:
        await session.execute(
            text("SELECT set_config('app.current_tenant_id', :tid, true)"),
            {"tid": str(tenant_id)},
        )


async def dispose_engines() -> None:
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("engines_disposed")
