"""Session factory + UnitOfWork (Sprint 1)."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional
import uuid

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text

from src.infrastructure.db.settings import settings

engine = create_async_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class UnitOfWork:
    def __init__(self, session: AsyncSession):
        self.session = session
        self._tenant_id: Optional[uuid.UUID] = None

    async def __aenter__(self) -> "UnitOfWork":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if exc_type:
            await self.session.rollback()
        else:
            await self.session.commit()

    async def set_current_tenant(self, papeleria_id: uuid.UUID) -> None:
        """Activa RLS para el tenant actual (SET LOCAL)."""
        self._tenant_id = papeleria_id
        await self.session.execute(
            text("SELECT set_config('app.current_papeleria_id', :pid, true)"),
            {"pid": str(papeleria_id)},
        )

    @property
    def tenant_id(self) -> Optional[uuid.UUID]:
        return self._tenant_id


@asynccontextmanager
async def get_uow() -> AsyncIterator[UnitOfWork]:
    async with SessionLocal() as session:
        async with UnitOfWork(session) as uow:
            yield uow
