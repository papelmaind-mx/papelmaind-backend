from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from src.core.config import get_settings

settings = get_settings()

api_engine = create_async_engine(
    settings.DATABASE_URL, pool_size=10, max_overflow=5,
    pool_recycle=300, pool_pre_ping=True, echo=False,
)
AsyncSessionLocal = async_sessionmaker(bind=api_engine, class_=AsyncSession, expire_on_commit=False)

worker_engine = create_async_engine(
    settings.WORKER_DATABASE_URL, pool_size=5, max_overflow=2,
    pool_recycle=300, pool_pre_ping=True, echo=False,
)
WorkerSessionLocal = async_sessionmaker(bind=worker_engine, class_=AsyncSession, expire_on_commit=False)
