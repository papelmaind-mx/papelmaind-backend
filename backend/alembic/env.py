import asyncio
import os
from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

config = context.config

def get_url() -> str:
    return os.getenv("ADMIN_DATABASE_URL", "postgresql+asyncpg://admin:admin_dev@localhost:5432/papelmind")

def run_migrations_offline() -> None:
    context.configure(url=get_url(), literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection) -> None:
    context.configure(connection=connection, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    engine = create_async_engine(get_url(), poolclass=None)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
