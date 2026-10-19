import asyncio
import os
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

ADMIN_URL = os.getenv("TEST_DATABASE_URL",
                      "postgresql+asyncpg://admin:admin_dev@localhost:5432/papelmind")
APP_URL = os.getenv("TEST_APP_URL",
                    "postgresql+asyncpg://erp_app:erp_app_dev@localhost:5432/papelmind")

from passlib.context import CryptContext
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
PWD = "TestAdmin123!"
HASH = pwd.hash(PWD)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def admin_engine():
    engine = create_async_engine(ADMIN_URL)
    async with engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: _run_alembic_upgrade(sync_conn))
    yield engine
    await engine.dispose()


def _run_alembic_upgrade(sync_conn):
    from alembic.config import Config
    from alembic import command
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", ADMIN_URL.replace("+asyncpg", "+psycopg2"))
    command.upgrade(cfg, "head")


@pytest_asyncio.fixture(scope="session")
async def seed_data(admin_engine):
    """Seed mínimo de test: tenants A/B + usuarios con contraseña conocida."""
    t_a, t_b = uuid.uuid4(), uuid.uuid4()
    u_a, u_b = uuid.uuid4(), uuid.uuid4()
    rel_a, rel_b = uuid.uuid4(), uuid.uuid4()
    async with admin_engine.begin() as conn:
        await conn.execute(text(
            "INSERT INTO papelerias (id, nombre, slug) VALUES "
            f"('{t_a}','Test A','test-a'), ('{t_b}','Test B','test-b')"))
        await conn.execute(text(
            "INSERT INTO tusuarios (id, username, display_name, password_hash, activo, verificado) VALUES "
            f"('{u_a}','test_admin_a','Admin A','{HASH}',true,true), "
            f"('{u_b}','test_admin_b','Admin B','{HASH}',true,true), "
            f"('{uuid.uuid4()}','test_inactive','Inactivo','{HASH}',false,true)"))
        await conn.execute(text(
            "INSERT INTO usuario_papeleria_rel (id, usuario_id, papeleria_id, rol) VALUES "
            f"('{rel_a}','{u_a}','{t_a}','admin'), ('{rel_b}','{u_b}','{t_b}','admin'), "
            f"('{uuid.uuid4()}','{(await conn.execute(text(\"SELECT id FROM tusuarios WHERE username='test_inactive'\"))).scalar()}','{t_a}','cajero')"))
    return {"t_a": t_a, "t_b": t_b, "u_a": u_a, "u_b": u_b,
            "rel_a": rel_a, "rel_b": rel_b, "pwd": PWD}


@pytest_asyncio.fixture
async def app_session(seed_data):
    """Sesión con rol erp_app (RLS activo) para asserts de aislamiento."""
    engine = create_async_engine(APP_URL)
    factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    session = factory()
    yield session
    await session.rollback()
    await session.close()
    await engine.dispose()


@pytest_asyncio.fixture
async def client(admin_engine, seed_data):
    from src.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
