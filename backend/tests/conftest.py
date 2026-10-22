"""Fixtures globales — canon Suite E2E (conftest.py).

BD de tests: SQLite en memoria por test (RLS emulado en capa app);
en CI se puede apuntar TEST_DATABASE_URL a PostgreSQL para RLS real.
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.core.config import settings
from src.core.security import get_password_hash
from src.infrastructure.db import models

# Override ANTES de crear engines: SQLite en memoria (RLS emulado)
settings.database_url = "sqlite+aiosqlite:///:memory:"
settings.test_database_url = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator:
    """Engine + schema nuevo por test → aislamiento total."""
    engine = create_async_engine(settings.database_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    session = factory()
    try:
        yield session
    finally:
        await session.rollback()
        await session.close()
        await engine.dispose()


@pytest_asyncio.fixture
async def app_client(db_session) -> AsyncIterator[AsyncClient]:
    """Cliente HTTP contra la app con la sesión de test inyectada."""
    from src.api.dependencies.db import get_db
    from src.main import app

    async def _override_get_db():
        try:
            yield db_session
        except Exception:
            # Igual que get_db en producción: excepción de dominio → rollback
            await db_session.rollback()
            raise
        else:
            # Igual que get_db en producción: éxito → commit
            await db_session.commit()

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


# ==================== Helpers de dominio ====================

async def _make_tenant(session, nombre: str, slug: str) -> models.Papeleria:
    tenant = models.Papeleria(nombre=nombre, slug=slug)
    session.add(tenant)
    await session.flush()
    return tenant


async def _make_user(session, username: str, password: str, tenant, rol: str = "admin"):
    user = models.TUsuario(
        username=username,
        display_name=username.title(),
        password_hash=get_password_hash(password),
    )
    session.add(user)
    await session.flush()
    rel = models.UsuarioPapeleriaRel(
        usuario_id=user.id, papeleria_id=tenant.id, rol=rol
    )
    session.add(rel)
    await session.flush()
    return user, rel


async def _make_catalog(session, tenant):
    """Unidad PZA + IVA 16% + artículo CUADERNO-100 con 2 lotes FEFO (T2)."""
    um = models.TUnidadMedida(papeleria_id=tenant.id, clave="PZA", nombre="Pieza")
    imp = models.TImpuesto(
        papeleria_id=tenant.id, nombre="IVA 16%", tipo="iva", tasa=Decimal("0.1600")
    )
    session.add_all([um, imp])
    await session.flush()
    art = models.TArticulo(
        papeleria_id=tenant.id,
        sku="CUADERNO-100",
        descripcion="Cuaderno Profesional 100 hojas",
        unidad_medida_id=um.id,
        impuesto_id=imp.id,
        precio_base=Decimal("35.5000"),
    )
    session.add(art)
    await session.flush()
    today = datetime.now(UTC).date()
    lote_cercano = models.TLote(
        papeleria_id=tenant.id,
        articulo_id=art.id,
        numero_lote="L-30D",
        fecha_vencimiento=today + timedelta(days=30),
        cantidad_actual=Decimal("10.000"),
        estado="disponible",
    )
    lote_lejano = models.TLote(
        papeleria_id=tenant.id,
        articulo_id=art.id,
        numero_lote="L-365D",
        fecha_vencimiento=today + timedelta(days=365),
        cantidad_actual=Decimal("20.000"),
        estado="disponible",
    )
    session.add_all([lote_cercano, lote_lejano])
    await session.flush()
    art.stock_actual = Decimal("30.000")
    await session.flush()
    return {
        "um": um,
        "imp": imp,
        "art": art,
        "lote_cercano": lote_cercano,
        "lote_lejano": lote_lejano,
    }


@pytest_asyncio.fixture
async def tenant_a(db_session):
    return await _make_tenant(db_session, "Papelería Central", "central-a")


@pytest_asyncio.fixture
async def tenant_b(db_session):
    return await _make_tenant(db_session, "Librería del Norte", "norte-b")


@pytest_asyncio.fixture
async def admin_a(db_session, tenant_a):
    return await _make_user(db_session, "admin_a", "AdminA123!", tenant_a, "admin")


@pytest_asyncio.fixture
async def admin_b(db_session, tenant_b):
    return await _make_user(db_session, "admin_b", "AdminB123!", tenant_b, "admin")


@pytest_asyncio.fixture
async def catalog_a(db_session, tenant_a):
    return await _make_catalog(db_session, tenant_a)


@pytest_asyncio.fixture
async def catalog_b_for_tenant_b(db_session, tenant_b):
    return await _make_catalog(db_session, tenant_b)


async def login(client: AsyncClient, username: str, password: str) -> dict:
    resp = await client.post(
        "/api/v1/auth/login", json={"username": username, "password": password}
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
