from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(default="development", alias="APP_ENV")

    database_url: str = Field(
        default="postgresql+psycopg://xianxia:xianxia@localhost:5432/xianxia_db",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_base_url: Optional[str] = Field(default=None, alias="OPENAI_BASE_URL")
    openai_model: str = Field(default="deepseek-chat", alias="OPENAI_MODEL")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small",
        alias="OPENAI_EMBEDDING_MODEL",
    )
    openai_embedding_base_url: Optional[str] = Field(
        default=None,
        alias="OPENAI_EMBEDDING_BASE_URL",
    )

    chroma_persist_dir: Path = Field(
        default=PROJECT_ROOT / "data" / "chroma",
        alias="CHROMA_PERSIST_DIR",
    )

    memory_recent_turns_max: int = Field(
        default=10,
        ge=2,
        le=50,
        alias="MEMORY_RECENT_TURNS_MAX",
    )
    memory_summary_max_chars: int = Field(
        default=1200,
        ge=200,
        le=8000,
        alias="MEMORY_SUMMARY_MAX_CHARS",
    )
    memory_max_tokens: int = Field(
        default=4000,
        ge=200,
        le=32000,
        alias="MEMORY_MAX_TOKENS",
    )

    api_host: str = Field(default="127.0.0.1", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    cors_origins: str = Field(
        default="http://localhost:8501,http://127.0.0.1:8501",
        alias="CORS_ORIGINS",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
