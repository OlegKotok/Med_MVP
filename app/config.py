from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Medical Patient Registration"
    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/med_mvp"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    # Settings are cached so dependency injection does not re-read the environment per request.
    return Settings()
