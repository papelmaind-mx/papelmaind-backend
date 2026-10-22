"""Migraciones — `python -m src.infrastructure.db.migrate [apply|create]`.

- SQLite (dev/test): crea el schema desde SQLAlchemy metadata (RLS emulado en app).
- PostgreSQL (prod): aplica los .sql de backend/migrations en orden
  (extensiones + tablas + RLS suite de docker/init-scripts).
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from sqlalchemy import text

from src.core.config import settings
from src.core.logging import configure_logging, logger
from src.infrastructure.db.models import Base
from src.infrastructure.db.session import dispose_engines, get_api_engine

BACKEND = Path(__file__).resolve().parents[3]  # backend/
REPO = BACKEND.parent                  # papelmaind/
MIGRATIONS_DIR = BACKEND / "migrations"
INIT_SCRIPTS_DIR = REPO / "docker" / "init-scripts"

ORDERED_SQL = [
    # init-scripts primero (extensiones, roles, funciones, RLS suite)
    INIT_SCRIPTS_DIR / "01-extensions.sql",
    INIT_SCRIPTS_DIR / "02-roles.sql",
    INIT_SCRIPTS_DIR / "03-functions.sql",
    INIT_SCRIPTS_DIR / "04-rls-suite.sql",
    # migraciones por sprint
    MIGRATIONS_DIR / "0001_s1_fundacion.sql",
    MIGRATIONS_DIR / "0002_s2_catalogo_inventario.sql",
]


async def apply_sqlite() -> None:
    engine = get_api_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    logger.info("migrate_sqlite_ok", tables=len(Base.metadata.tables))


async def apply_postgres() -> None:
    engine = get_api_engine()
    applied: list[str] = []
    async with engine.begin() as conn:
        await conn.execute(
            text("CREATE TABLE IF NOT EXISTS schema_migrations ("
                 "version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ DEFAULT now())")
        )
        for sql_path in ORDERED_SQL:
            if not sql_path.exists():
                logger.warning("migration_missing", path=str(sql_path))
                continue
            # exec_driver_sql permite multi-statement (asyncpg lo requiere así)
            await conn.exec_driver_sql(sql_path.read_text(encoding="utf-8"))
            await conn.execute(
                text("INSERT INTO schema_migrations (version) VALUES (:v)"),
                {"v": sql_path.name},
            )
            applied.append(sql_path.name)
    logger.info("migrate_postgres_ok", applied=applied)


async def main() -> int:
    configure_logging(settings.log_level)
    try:
        if settings.is_sqlite:
            await apply_sqlite()
        else:
            await apply_postgres()
        return 0
    except Exception as e:  # pragma: no cover
        logger.error("migrate_failed", error=str(e))
        return 1
    finally:
        await dispose_engines()


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "apply"
    if cmd != "apply":
        print("Uso: python -m src.infrastructure.db.migrate apply")
        sys.exit(2)
    sys.exit(asyncio.run(main()))
