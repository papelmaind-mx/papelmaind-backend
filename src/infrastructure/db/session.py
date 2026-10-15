"""Session factory + UnitOfWork (Sprint 1)."""
from contextlib import asynccontextmanager
from typing import AsyncIterator

# from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
# Implementar en S1:
# - get_session()
# - UnitOfWork con set_current_tenant(papeleria_id)
# - commit / rollback explícitos

class UnitOfWork:
    """Esqueleto — completar en Sprint 1."""
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if exc_type:
            await self.session.rollback()
        else:
            await self.session.commit()

    async def set_current_tenant(self, papeleria_id: str) -> None:
        # SET LOCAL app.current_papeleria_id = ...
        raise NotImplementedError("S1")
