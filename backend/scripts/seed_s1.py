"""Seed S1: 2 tenants + admins + sucursales + claves config."""
import asyncio
import os
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

ADMIN_URL = os.getenv(
    "ADMIN_DATABASE_URL",
    "postgresql+asyncpg://admin:admin_dev@localhost:5432/papelmind",
)

CLAVES_F24 = [
    ("logo_url", "null"),
    ("colores_json", "{}"),
    ("impuesto_default_pct", "16.00"),
    ("moneda_default", "MXN"),
    ("zona_horaria", "America/Mexico_City"),
    ("ticket_header", "PapelMind Demo"),
    ("ticket_footer", "Gracias por su compra"),
    ("whatsapp_phone_number_id", "null"),
    ("google_calendar_id", "null"),
    ("print_mode", "office"),
    ("peso_validacion", "advertencia"),
    ("enganche_pct_default", "30.00"),
    ("plazo_aparado_dias", "30"),
    ("tolerancia_precio_json", '{"pct":5,"abs":20}'),
    ("envio_gratis_desde", "499.00"),
    ("drawer_continuity", "true"),
    ("dlq_alerta_email_threshold", "20"),
    ("dlq_alerta_cfdi_threshold", "50"),
]

import bcrypt as _bcrypt
def _hash(pw: str) -> str:
    return _bcrypt.hashpw(pw.encode(), _bcrypt.gensalt()).decode()
HASH_A = _hash("AdminA123!")
HASH_B = _hash("AdminB123!")


async def seed() -> None:
    engine = create_async_engine(ADMIN_URL)
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "TRUNCATE tauditlogs, usuario_verificaciones, "
                "usuario_sesiones, usuario_papeleria_rel, "
                "papeleria_configuracion, sucursales, tusuarios, "
                "papelerias CASCADE"
            )
        )
        t_a, t_b = uuid.uuid4(), uuid.uuid4()
        await conn.execute(
            text(
                "INSERT INTO papelerias (id, nombre, slug, plan) VALUES "
                "(:a, 'Papeleria Demo A', 'demo-a', 'profesional'), "
                "(:b, 'Papeleria Demo B', 'demo-b', 'basico')"
            ),
            {"a": t_a, "b": t_b},
        )

        u_a, u_b = uuid.uuid4(), uuid.uuid4()
        await conn.execute(
            text(
                "INSERT INTO tusuarios "
                "(id, username, display_name, email, password_hash, verificado) VALUES "
                "(:ua, 'admin_a', 'Admin Demo A', 'admin.a@demo.mx', :ha, true), "
                "(:ub, 'admin_b', 'Admin Demo B', 'admin.b@demo.mx', :hb, true)"
            ),
            {"ua": u_a, "ub": u_b, "ha": HASH_A, "hb": HASH_B},
        )

        for t, u in ((t_a, u_a), (t_b, u_b)):
            await conn.execute(
                text(
                    "INSERT INTO usuario_papeleria_rel "
                    "(id, usuario_id, papeleria_id, rol) VALUES "
                    "(:id, :u, :t, 'admin')"
                ),
                {"id": uuid.uuid4(), "u": u, "t": t},
            )
            await conn.execute(
                text(
                    "INSERT INTO sucursales "
                    "(id, papeleria_id, nombre, codigo, es_default) VALUES "
                    "(:id, :t, 'Sucursal Centro', 'CEN', true)"
                ),
                {"id": uuid.uuid4(), "t": t},
            )
            for clave, valor in CLAVES_F24:
                await conn.execute(
                    text(
                        "INSERT INTO papeleria_configuracion "
                        "(id, papeleria_id, clave, valor) VALUES "
                        "(:id, :t, :c, :v)"
                    ),
                    {"id": uuid.uuid4(), "t": t, "c": clave, "v": valor},
                )

        await conn.execute(
            text(
                "INSERT INTO currencies (codigo, nombre, simbolo) VALUES "
                "('MXN', 'Peso Mexicano', '$'), ('USD', 'Dolar', 'US$') "
                "ON CONFLICT DO NOTHING"
            )
        )
        await conn.execute(
            text(
                "INSERT INTO lenguajes (codigo, nombre, nombre_nativo) VALUES "
                "('es', 'Espanol', 'Espanol'), ('en', 'English', 'English') "
                "ON CONFLICT DO NOTHING"
            )
        )

    await engine.dispose()
    print("✅ Seed S1 OK — admin_a/AdminA123! · admin_b/AdminB123!")


if __name__ == "__main__":
    asyncio.run(seed())
