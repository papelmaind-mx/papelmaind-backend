"""Seed data para tests — canon backend/tests/fixtures/seed_data.py.

Helpers reutilizables por la suite E2E: tenants, usuarios, catálogo con lotes FEFO.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from src.core.security import get_password_hash
from src.infrastructure.db import models


async def seed_tenant(session, nombre: str, slug: str) -> models.Papeleria:
    tenant = models.Papeleria(nombre=nombre, slug=slug)
    session.add(tenant)
    await session.flush()
    return tenant


async def seed_user(session, username: str, password: str, tenant, rol: str) -> models.TUsuario:
    user = models.TUsuario(
        username=username,
        display_name=username.title(),
        password_hash=get_password_hash(password),
    )
    session.add(user)
    await session.flush()
    session.add(
        models.UsuarioPapeleriaRel(
            usuario_id=user.id, papeleria_id=tenant.id, rol=rol
        )
    )
    await session.flush()
    return user


async def seed_catalog_with_lotes(
    session,
    tenant,
    *,
    sku: str = "CUADERNO-100",
    lote_cercano_qty: str = "10.000",
    lote_lejano_qty: str = "20.000",
) -> dict:
    """Catálogo T2: 2 lotes (vence 30d vs 365d) — base del test fefo_orden."""
    um = models.TUnidadMedida(papeleria_id=tenant.id, clave="PZA", nombre="Pieza")
    imp = models.TImpuesto(
        papeleria_id=tenant.id, nombre="IVA 16%", tipo="iva", tasa=Decimal("0.1600")
    )
    session.add_all([um, imp])
    await session.flush()
    art = models.TArticulo(
        papeleria_id=tenant.id,
        sku=sku,
        descripcion=f"Artículo {sku}",
        unidad_medida_id=um.id,
        impuesto_id=imp.id,
        precio_base=Decimal("35.5000"),
    )
    session.add(art)
    await session.flush()

    today = datetime.now(UTC).date()
    cercano = models.TLote(
        papeleria_id=tenant.id,
        articulo_id=art.id,
        numero_lote=f"{sku}-30D",
        fecha_vencimiento=today + timedelta(days=30),
        cantidad_actual=Decimal(lote_cercano_qty),
        estado="disponible",
    )
    lejano = models.TLote(
        papeleria_id=tenant.id,
        articulo_id=art.id,
        numero_lote=f"{sku}-365D",
        fecha_vencimiento=today + timedelta(days=365),
        cantidad_actual=Decimal(lote_lejano_qty),
        estado="disponible",
    )
    session.add_all([cercano, lejano])
    await session.flush()
    art.stock_actual = Decimal(lote_cercano_qty) + Decimal(lote_lejano_qty)
    await session.flush()
    return {"um": um, "imp": imp, "art": art, "lote_cercano": cercano, "lote_lejano": lejano}


async def seed_admin_a_and_b(session) -> dict:
    """2 tenants + admin en cada uno — base del test T5 rls_disjoint."""
    tenant_a = await seed_tenant(session, "Papelería Central", "central-a")
    tenant_b = await seed_tenant(session, "Librería del Norte", "norte-b")
    await seed_user(session, "admin_a", "AdminA123!", tenant_a, "admin")
    await seed_user(session, "admin_b", "AdminB123!", tenant_b, "admin")
    await session.commit()
    return {"tenant_a": tenant_a, "tenant_b": tenant_b}
