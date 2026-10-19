from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://erp_app:erp_app_dev@localhost:5432/papelmind"
    WORKER_DATABASE_URL: str = "postgresql+asyncpg://erp_worker:erp_worker_dev@localhost:5432/papelmind"
    JWT_SECRET: str = "dev_secret_cambiar_min_32_chars_aqui!"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    PRE_TOKEN_EXPIRE_MINUTES: int = 10
    REFRESH_TOKEN_EXPIRE_HOURS: int = 8
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache
def get_settings() -> Settings:
    return Settings()
