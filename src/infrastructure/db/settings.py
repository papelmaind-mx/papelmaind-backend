from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://papelmind:papelmind@localhost:5432/papelmind"
    jwt_secret: str = "CHANGE_ME_DEV_ONLY"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480
    app_name: str = "PapelMind"


settings = Settings()
