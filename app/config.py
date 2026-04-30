from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    # JWT — generate a strong secret: python -c "import secrets; print(secrets.token_hex(32))"
    JWT_SECRET: str = "change-me-in-production"
    JWT_EXPIRE_MINUTES: int = 60

    # Email — leave SMTP_HOST empty to use console logging (demo mode)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@example.com"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
