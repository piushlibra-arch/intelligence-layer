from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Adaptive Trader Risk Intelligence"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://trader_risk:postgres@localhost:5432/trader_risk_intel",
        description="Async database connection string"
    )
    DATABASE_URL_SYNC: str = Field(
        default="postgresql://trader_risk:postgres@localhost:5432/trader_risk_intel",
        description="Sync database connection string for alembic"
    )
    API_KEY: str = Field(default="dev-api-key-not-for-production")
    CORS_ORIGINS: str = Field(default="http://localhost:5173,http://localhost:3000,http://localhost,http://127.0.0.1:5173")
    LOG_LEVEL: str = Field(default="INFO")
    ENGINE_VERSION: str = Field(default="1.0.0")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

settings = Settings()
