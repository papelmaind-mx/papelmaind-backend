"""TenantUnitOfWork — canon CONV-07.

Unidad de trabajo transaccional con contexto de tenant:
- PostgreSQL 16 (prod): `SET LOCAL app.current_tenant_id` + políticas RLS reales
  (ver docker/init-scripts/04-rls-suite.sql y backend/migrations/*.sql).
- SQLite (dev/test sin Docker): RLS EMULADO — cada consulta de repositorio
  filtra explícitamente por papeleria_id tomado del contexto de sesión.

La emulación garantiza el mismo contrato de aislamiento (verificado por test T5
rls_disjoint) hasta desplegar en PostgreSQL con RLS nativo.
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.db.session import (
    get_session_factory,
    set_tenant_context,
)


class TenantUnitOfWork:
    """Agrupa una sesión + contexto tenant en una sola transacción lógica."""

    def __init__(self, tenant_id: UUID | str) -> None:
        self.tenant_id = str(tenant_id)
        self.session: AsyncSession | None = None

    async def __aenter__(self) -> TenantUnitOfWork:
        factory = get_session_factory()
        self.session = factory()
        await set_tenant_context(self.session, self.tenant_id)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self.session is None:
            return
        if exc_type is None:
            await self.session.commit()
        else:
            await self.session.rollback()
        await self.session.close()
        self.session = None

    @property
    def db(self) -> AsyncSession:
        if self.session is None:
            raise RuntimeError("TenantUnitOfWork usado fuera de contexto async with")
        return self.session


@asynccontextmanager
async def tenant_session(tenant_id: UUID | str) -> AsyncIterator[AsyncSession]:
    """Helper: sesión con commit/rollback automático y contexto tenant."""
    factory = get_session_factory()
    session = factory()
    try:
        await set_tenant_context(session, str(tenant_id))
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
