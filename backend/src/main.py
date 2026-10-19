from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from src.core.database import api_engine
from src.api.v1 import auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await api_engine.dispose()

app = FastAPI(title="PapelMind API", version="0.1.0-s1", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router, prefix="/api/v1")

@app.get("/health", tags=["infra"])
async def health():
    return {"status": "ok"}

@app.get("/ready", tags=["infra"])
async def ready():
    async with api_engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return {"status": "ready", "db": "up"}
