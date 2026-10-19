from types import TracebackType
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import AsyncSessionLocal

class TenantUnitOfWork:
    def __init__(self, tenant_id: UUID):
        self.tenant_id = tenant_id
        self.session: AsyncSession | None = None
        self.tx = None

    async def __aenter__(self) -> AsyncSession:
        self.session = AsyncSessionLocal()
        self.tx = await self.session.begin()
        await self.session.execute(
            text("SELECT set_current_tenant(:t)"), {"t": str(self.tenant_id)}
        )
        return self.session

    async def __aexit__(
        self, exc_type: type[BaseException] | None,
        exc_val: BaseException | None, exc_tb: TracebackType | None,
    ) -> None:
        if not self.session or not self.tx:
            return
        try:
            if exc_type:
                await self.tx.rollback()
            else:
                await self.tx.commit()
        finally:
            await self.session.close()
