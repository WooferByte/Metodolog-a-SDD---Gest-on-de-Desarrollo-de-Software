"""
Application configuration using Pydantic BaseSettings.

Loads configuration from environment variables (.env file).
Supports development, test, and production modes.
"""
from typing import Any
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    env: str = Field(default="development", alias="ENV")
    app_name: str = Field(default="Food Store API", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")

    # Database
    database_url: str = Field(..., alias="DATABASE_URL")
    database_pool_size: int = Field(default=20, alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=10, alias="DATABASE_MAX_OVERFLOW")

    # Security & JWT
    secret_key: str = Field(..., alias="SECRET_KEY")
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")
    bcrypt_cost: int = Field(default=10, alias="BCRYPT_COST")

    # CORS - can be string (comma-separated) or list
    cors_origins: list[str] | str = Field(
        default="http://localhost:3000",
        alias="CORS_ORIGINS"
    )

    # MercadoPago
    mercadopago_access_token: str = Field(default="", alias="MERCADOPAGO_ACCESS_TOKEN")
    mercadopago_public_key: str = Field(default="", alias="MERCADOPAGO_PUBLIC_KEY")

    # Rate Limiting
    rate_limit_login: int = Field(default=5, alias="RATE_LIMIT_LOGIN")
    rate_limit_window: int = Field(default=900, alias="RATE_LIMIT_WINDOW")  # 15 minutes

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Allow environment variable names to be case-insensitive
        case_sensitive = False
        # Populate by name to allow both snake_case and UPPER_CASE
        populate_by_name = True

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        """Parse comma-separated CORS origins string into list."""
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return ["http://localhost:3000"]

    def is_dev(self) -> bool:
        """Check if running in development mode."""
        return self.env == "development"

    def is_test(self) -> bool:
        """Check if running in test mode."""
        return self.env == "test"

    def is_prod(self) -> bool:
        """Check if running in production mode."""
        return self.env == "production"


# Singleton instance - loaded on module import
settings = Settings()


