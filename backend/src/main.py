"""PapelMaind API — entrypoint FastAPI (canon Sección 11: backend/src/main.py)."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.api.v1.router import api_router
from src.core.config import settings
from src.core.exceptions import (
    AuthenticationError,
    DuplicateEntityError,
    ForbiddenError,
    NotFoundError,
    PapelMaindError,
)
from src.core.logging import configure_logging, logger
from src.core.metrics import inc_counter
from src.infrastructure.db import migrate as db_migrate
from src.infrastructure.db import seed as db_seed
from src.infrastructure.db.session import dispose_engines


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings.log_level)
    logger.info("startup", app=settings.app_name, env=settings.app_env)
    if settings.is_sqlite:
        # Dev sin Docker: schema + seed automáticos (prod: compose ejecuta migrate/seed)
        await db_migrate.apply_sqlite()
        await db_seed.main()
    yield
    await dispose_engines()
    logger.info("shutdown")


app = FastAPI(
    title=settings.app_name,
    description="PapelMaind — Plataforma Omnicanal Multi-Tenant para Cadenas de Papelerías",
    version="2.3.0",
    lifespan=lifespan,
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


# ---------- Manejo de errores de dominio (CONV-05: HTTP solo en capa API) ----------
@app.exception_handler(AuthenticationError)
async def _auth_error(_: Request, exc: AuthenticationError) -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": str(exc)})


@app.exception_handler(ForbiddenError)
async def _forbidden_error(_: Request, exc: ForbiddenError) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": str(exc)})


@app.exception_handler(NotFoundError)
async def _not_found_error(_: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(DuplicateEntityError)
async def _duplicate_error(_: Request, exc: DuplicateEntityError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(PapelMaindError)
async def _domain_error(_: Request, exc: PapelMaindError) -> JSONResponse:
    inc_counter("erp_domain_errors_total", {"type": type(exc).__name__})
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.middleware("http")
async def _metrics_middleware(request: Request, call_next):
    inc_counter("erp_http_requests_total", {"method": request.method})
    response = await call_next(request)
    inc_counter(
        "erp_http_request_duration_seconds",
        {"method": request.method, "status_code": str(response.status_code)},
    )
    return response
