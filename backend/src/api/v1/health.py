"""Router /health — liveness, readiness y métricas (canon observabilidad)."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.db import get_db
from src.core.config import settings
from src.core.metrics import render_metrics

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness probe")
async def health() -> dict:
    return {"status": "ok", "app": settings.app_name, "env": settings.app_env}


@router.get("/ready", summary="Readiness probe (BD accesible)")
async def ready(db: Annotated[AsyncSession, Depends(get_db)]) -> dict:
    await db.execute(text("SELECT 1"))
    tenants = (
        await db.execute(text("SELECT count(*) FROM papelerias"))
    ).scalar()
    return {"status": "ready", "db": "ok", "tenants": tenants}


@router.get("/metrics", summary="Métricas Prometheus (text/plain)")
async def metrics() -> dict:
    from fastapi.responses import PlainTextResponse  # noqa: PLC0415

    return PlainTextResponse(render_metrics())  # type: ignore[return-value]
