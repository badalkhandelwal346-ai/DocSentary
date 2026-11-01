from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "DocSentry"
    VERSION: str = "0.2.0"
    API_V1_STR: str = "/api/v1"
    DOCSENTRY_ENV: str = "development"

    # Database
    # Defaults to local SQLite file for seamless zero-setup development and testing,
    # and supports PostgreSQL in production via postgresql+psycopg://
    DATABASE_URL: str = "sqlite:///./docsentry.db"

    # Security
    SECRET_KEY: str = "docsentry-insecure-dev-secret-key-change-in-production-1234567890"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ALGORITHM: str = "HS256"

    # GitHub App Integration
    GITHUB_CLIENT_ID: str | None = None
    GITHUB_CLIENT_SECRET: str | None = None
    GITHUB_WEBHOOK_SECRET: str | None = None
    GITHUB_APP_ID: str | None = None
    GITHUB_PRIVATE_KEY: str | None = None

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Analysis Engine execution settings
    DEFAULT_ANALYSIS_TIMEOUT_SECONDS: int = 120
    DEFAULT_DOCS_GLOBS: List[str] = ["docs/**/*.md", "README.md", "*.md"]
    DEFAULT_SOURCE_GLOBS: List[str] = ["src/**/*.py", "**/*.py"]
    DEFAULT_EXCLUDE_GLOBS: List[str] = [
        "tests/**",
        ".git/**",
        ".venv/**",
        "node_modules/**",
        "dist/**",
        "build/**",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
