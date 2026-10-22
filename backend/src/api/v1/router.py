"""Router v1 — agrega todos los módulos de la API (CHK-01)."""
from __future__ import annotations

from fastapi import APIRouter

from src.api.v1 import auth, catalog, health, inventory, pos, stubs, tenants

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(tenants.router)
api_router.include_router(catalog.router)
api_router.include_router(inventory.router)
api_router.include_router(pos.router)
api_router.include_router(stubs.stub_router)
