from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str = "change-me-in-production"
    JWT_EXPIRE_MINUTES: int = 60

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@example.com"
    # Set True for implicit TLS (port 465, e.g. ukr.net, Gmail).
    # Set False for STARTTLS (port 587).
    SMTP_USE_SSL: bool = False

    # Simple in-process rate limiting for auth endpoints (requests per minute per IP).
    # For production, replace with Redis-backed slowapi or nginx rate limiting.
    RATE_LIMIT_AUTH: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",  # ignore POSTGRES_* and any other docker-compose vars
    )


settings = Settings()
