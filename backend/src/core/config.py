"""Configuración central — canon Sección 1 (<variables_entorno>)."""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Aplicación
    app_name: str = "PapelMaind API"
    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = True
    app_port: int = 8000
    api_v1_prefix: str = "/api/v1"

    # Base de datos (dev sin Docker: SQLite + RLS emulado; prod: PostgreSQL 16 + RLS real)
    database_url: str = "sqlite+aiosqlite:///./papelmaind_dev.db"
    test_database_url: str = "sqlite+aiosqlite:///./papelmaind_test.db"

    @field_validator("database_url", "test_database_url", mode="before")
    @classmethod
    def _only_sqlalchemy_urls(cls, v: object, info) -> object:
        """Ignora DATABASE_URL ambientales que no son URLs SQLAlchemy válidas.

        p.ej. el sandbox inyecta DATABASE_URL=file:/... (un solo '/'), que no
        es parseable por SQLAlchemy. Solo aceptamos scheme://... — si no,
        se usa el default del campo.
        """
        if isinstance(v, str) and v and "://" not in v:
            return cls.model_fields[info.field_name].default
        return v

    # Seguridad (canon <auth>: access 15min · refresh ROTACIÓN)
    jwt_secret: str = "dev-secret-cambiar-en-produccion"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_hours: int = 24

    # Redis (producción)
    redis_url: str = "redis://localhost:6379/0"

    # PAC CFDI (S7) — T10 cfdi_pac_fallback
    pac_primary_url: str = "https://demo-pac-primary.example/timbrado"
    pac_fallback_url: str = "https://demo-pac-fallback.example/timbrado"
    pac_timeout_seconds: float = 10.0

    # Observabilidad
    log_level: str = "INFO"

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
