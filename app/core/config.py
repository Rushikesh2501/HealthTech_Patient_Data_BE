"""Application configuration using Pydantic Settings v2.
Supports environment files and optional AWS Secrets Manager resolution.
"""

import json
import logging
from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env.development", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # General
    APP_NAME: str = "HealthTech Patient Data Dashboard API"
    APP_ENV: str = "development"
    DEBUG: bool = False
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Database
    DATABASE_URL: str = "postgresql+psycopg://postgres:password@localhost:5432/healthtech"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # JWT Security
    JWT_SECRET_KEY: str = "insecure-dev-jwt-secret-replace-in-production-min-32-chars"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Google Gemini AI
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
    ]

    # AWS
    AWS_REGION: str = "us-east-1"
    AWS_SECRET_NAME: str = ""
    USE_AWS_IAM_AUTH: bool = False

    # Supabase (Optional keys for extended Supabase integrations)
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    # Logging
    LOG_LEVEL: str = "INFO"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"


def load_aws_secrets(secret_name: str, region_name: str) -> dict:
    """Fetch secrets from AWS Secrets Manager if running inside AWS production.
    Fails safely and falls back to environment variables if boto3/credentials are absent.
    """
    try:
        import boto3

        client = boto3.client("secretsmanager", region_name=region_name)
        response = client.get_secret_value(SecretId=secret_name)
        if "SecretString" in response:
            return json.loads(response["SecretString"])
    except Exception as e:
        logger.warning(
            "Could not fetch secrets from AWS Secrets Manager (%s): %s. "
            "Falling back to local environment variables.",
            secret_name,
            e,
        )
    return {}


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()

    # If AWS_SECRET_NAME is specified in production, override sensitive keys from AWS Secrets Manager
    if settings.AWS_SECRET_NAME and settings.is_production():
        aws_secrets = load_aws_secrets(settings.AWS_SECRET_NAME, settings.AWS_REGION)
        for key, value in aws_secrets.items():
            if hasattr(settings, key):
                setattr(settings, key, value)

    return settings


settings = get_settings()
