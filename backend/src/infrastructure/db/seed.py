"""Seed inicial — canon CHK-09/CHK-10.

Crea:
- 2 tenants: Papelería Central (A) y Librería del Norte (B) — para T5 rls_disjoint
- Usuarios: admin_a / AdminA123!, admin_b / AdminB123!, cajero01 / Cajero123! (tenant A)
- Sucursal matriz + estación POS-001 + caja 001 (tenant A)
- Unidades de medida base (PZA, KG, CJA, PQT) por tenant
- Impuestos base (IVA 16%, IVA 0%, Exento) por tenant

Idempotente: no duplica si ya existe (slug / username / clave).
"""
from __future__ import annotations

import asyncio
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.logging import configure_logging, logger
from src.core.security import get_password_hash
from src.infrastructure.db.models import (
    CajaRegistradora,
    Estacion,
    Papeleria,
    Sucursal,
    TImpuesto,
    TUnidadMedida,
    TUsuario,
    UsuarioPapeleriaRel,
)
from src.infrastructure.db.session import dispose_engines, get_session_factory

TENANTS = [
    {"nombre": "Papelería Central", "slug": "central"},
    {"nombre": "Librería del Norte", "slug": "norte"},
]

USERS = [
    {
        "username": "admin_a",
        "password": "AdminA123!",
        "display_name": "Administradora Central",
        "tenant_slug": "central",
        "rol": "admin",
    },
    {
        "username": "admin_b",
        "password": "AdminB123!",
        "display_name": "Administrador Norte",
        "tenant_slug": "norte",
        "rol": "admin",
    },
    {
        "username": "cajero01",
        "password": "Cajero123!",
        "display_name": "Cajero Turno Matutino",
        "tenant_slug": "central",
        "rol": "cajero",
    },
]

UNIDADES = [
    {"clave": "PZA", "nombre": "Pieza", "permite_decimales": False},
    {"clave": "KG", "nombre": "Kilogramo", "permite_decimales": True},
    {"clave": "CJA", "nombre": "Caja", "permite_decimales": False},
    {"clave": "PQT", "nombre": "Paquete", "permite_decimales": False},
]

IMPUESTOS = [
    {"nombre": "IVA 16%", "tipo": "iva", "tasa": Decimal("0.1600")},
    {"nombre": "IVA 0%", "tipo": "iva", "tasa": Decimal("0.0000")},
    {"nombre": "Exento", "tipo": "exento", "tasa": Decimal("0.0000")},
]


async def seed(session: AsyncSession) -> dict:
    stats: dict[str, int] = {"tenants": 0, "usuarios": 0, "unidades": 0, "impuestos": 0,
                             "sucursales": 0, "estaciones": 0, "cajas": 0}

    # 1) Tenants
    tenant_by_slug: dict[str, Papeleria] = {}
    for t in TENANTS:
        existing = (
            await session.execute(select(Papeleria).where(Papeleria.slug == t["slug"]))
        ).scalar_one_or_none()
        if existing is None:
            existing = Papeleria(nombre=t["nombre"], slug=t["slug"])
            session.add(existing)
            stats["tenants"] += 1
        tenant_by_slug[t["slug"]] = existing
    await session.flush()

    # 2) Usuarios + relación rol
    for u in USERS:
        user = (
            await session.execute(select(TUsuario).where(TUsuario.username == u["username"]))
        ).scalar_one_or_none()
        tenant = tenant_by_slug[u["tenant_slug"]]
        if user is None:
            user = TUsuario(
                username=u["username"],
                display_name=u["display_name"],
                password_hash=get_password_hash(u["password"]),
                is_active=True,
            )
            session.add(user)
            await session.flush()
            stats["usuarios"] += 1
        rel = (
            await session.execute(
                select(UsuarioPapeleriaRel).where(
                    UsuarioPapeleriaRel.usuario_id == user.id,
                    UsuarioPapeleriaRel.papeleria_id == tenant.id,
                )
            )
        ).scalar_one_or_none()
        if rel is None:
            session.add(
                UsuarioPapeleriaRel(
                    usuario_id=user.id, papeleria_id=tenant.id, rol=u["rol"]
                )
            )

    # 3) Catálogo base por tenant (unidades + impuestos)
    for tenant in tenant_by_slug.values():
        for um in UNIDADES:
            exists = (
                await session.execute(
                    select(TUnidadMedida).where(
                        TUnidadMedida.papeleria_id == tenant.id,
                        TUnidadMedida.clave == um["clave"],
                    )
                )
            ).scalar_one_or_none()
            if exists is None:
                session.add(TUnidadMedida(papeleria_id=tenant.id, **um))
                stats["unidades"] += 1
        for imp in IMPUESTOS:
            exists = (
                await session.execute(
                    select(TImpuesto).where(
                        TImpuesto.papeleria_id == tenant.id,
                        TImpuesto.nombre == imp["nombre"],
                    )
                )
            ).scalar_one_or_none()
            if exists is None:
                session.add(TImpuesto(papeleria_id=tenant.id, **imp))
                stats["impuestos"] += 1

    # 4) Sucursal matriz + caja + estación POS (tenant A)
    central = tenant_by_slug["central"]
    suc = (
        await session.execute(
            select(Sucursal).where(
                Sucursal.papeleria_id == central.id, Sucursal.codigo == "MATRIZ"
            )
        )
    ).scalar_one_or_none()
    if suc is None:
        suc = Sucursal(papeleria_id=central.id, nombre="Matriz Centro", codigo="MATRIZ")
        session.add(suc)
        await session.flush()
        stats["sucursales"] += 1
    caja = (
        await session.execute(
            select(CajaRegistradora).where(
                CajaRegistradora.papeleria_id == central.id,
                CajaRegistradora.codigo == "CAJA-001",
            )
        )
    ).scalar_one_or_none()
    if caja is None:
        caja = CajaRegistradora(
            papeleria_id=central.id,
            sucursal_id=suc.id,
            codigo="CAJA-001",
            tipo="fisica",
            fondo_fijo_default=Decimal("500.00"),
        )
        session.add(caja)
        await session.flush()
        stats["cajas"] += 1
    est = (
        await session.execute(
            select(Estacion).where(
                Estacion.papeleria_id == central.id, Estacion.codigo == "P01"
            )
        )
    ).scalar_one_or_none()
    if est is None:
        session.add(
            Estacion(
                papeleria_id=central.id,
                sucursal_id=suc.id,
                codigo="P01",
                tipo="POS",  # F26: MAYÚSCULAS
                caja_id=caja.id,
            )
        )
        stats["estaciones"] += 1

    await session.commit()
    return stats


async def verify(session: AsyncSession) -> list[str]:
    """CHK-10: verificación post-seed. Devuelve lista de errores (vacía = OK)."""
    errors: list[str] = []
    for u in USERS:
        user = (
            await session.execute(select(TUsuario).where(TUsuario.username == u["username"]))
        ).scalar_one_or_none()
        if user is None or not user.password_hash:
            errors.append(f"usuario {u['username']} faltante o sin password")
        else:
            rel = (
                await session.execute(
                    select(UsuarioPapeleriaRel).where(
                        UsuarioPapeleriaRel.usuario_id == user.id
                    )
                )
            ).scalar_one_or_none()
            if rel is None:
                errors.append(f"usuario {u['username']} sin relación tenant (rol)")
    for t in TENANTS:
        p = (
            await session.execute(select(Papeleria).where(Papeleria.slug == t["slug"]))
        ).scalar_one_or_none()
        if p is None:
            errors.append(f"tenant {t['slug']} faltante")
    return errors


async def main() -> int:
    configure_logging(settings.log_level)
    factory = get_session_factory()
    try:
        async with factory() as session:
            stats = await seed(session)
            errors = await verify(session)
        logger.info("seed_ok", **stats, errors=errors)
        if errors:
            return 1
        return 0
    except Exception as e:
        logger.error("seed_failed", error=str(e))
        return 1
    finally:
        await dispose_engines()


if __name__ == "__main__":
    sys_code = asyncio.run(main())
    raise SystemExit(sys_code)
