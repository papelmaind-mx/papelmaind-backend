"""Seed mínimo Sprint 1: 1 papelería, 1 sucursal, 1 admin, 18 claves F24."""
from __future__ import annotations

import asyncio
from sqlalchemy import select

from src.infrastructure.db.session import SessionLocal
from src.infrastructure.auth.jwt import hash_password
from src.domain.models.identity import (
    Papeleria, Sucursal, Usuario, UsuarioPapeleriaRel, CatalogoClavesConfig,
)

CLAVES = [
    ("zona_horaria", "string", "America/Mexico_City", "papeleria"),
    ("moneda", "string", "MXN", "papeleria"),
    ("iva_default", "decimal", "0.16", "papeleria"),
    ("peso_validacion", "string", "advertencia", "papeleria"),
    ("stock_minimo_default", "int", "5", "sucursal"),
    ("reserva_carrito_minutos", "int", "30", "papeleria"),
    ("folio_prefijo", "string", "PM", "papeleria"),
    ("cfdi_serie", "string", "A", "papeleria"),
    ("cfdi_lugar_expedicion", "string", "", "papeleria"),
    ("whatsapp_enabled", "bool", "false", "papeleria"),
    ("loyalty_enabled", "bool", "true", "papeleria"),
    ("kafka_enabled", "bool", "false", "global"),
    ("outbox_batch_size", "int", "50", "global"),
    ("dlq_max_intentos", "int", "5", "global"),
    ("pos_offline_max_horas", "int", "72", "papeleria"),
    ("arqueo_tolerancia", "decimal", "0.50", "sucursal"),
    ("session_ttl_minutos", "int", "480", "global"),
    ("feature_aparados", "bool", "false", "papeleria"),
]


async def main() -> None:
    async with SessionLocal() as session:
        # Claves F24
        for clave, tipo, default, ambito in CLAVES:
            exists = await session.scalar(
                select(CatalogoClavesConfig).where(CatalogoClavesConfig.clave == clave)
            )
            if not exists:
                session.add(CatalogoClavesConfig(
                    clave=clave, tipo=tipo, valor_default=default,
                    ambito=ambito, descripcion=f"Canon F24: {clave}",
                ))

        pap = await session.scalar(select(Papeleria).limit(1))
        if not pap:
            pap = Papeleria(nombre="Papelería Demo", rfc="XAXX010101000")
            session.add(pap)
            await session.flush()
            session.add(Sucursal(papeleria_id=pap.id, nombre="Sucursal Centro"))

        user = await session.scalar(select(Usuario).where(Usuario.email == "admin@papelmind.local"))
        if not user:
            user = Usuario(
                email="admin@papelmind.local",
                password_hash=hash_password("admin123"),
                nombre="Admin Demo",
            )
            session.add(user)
            await session.flush()
            session.add(UsuarioPapeleriaRel(
                usuario_id=user.id, papeleria_id=pap.id, rol="admin",
            ))

        await session.commit()
        print("✅ Seed S1 OK — admin@papelmind.local / admin123")


if __name__ == "__main__":
    asyncio.run(main())
