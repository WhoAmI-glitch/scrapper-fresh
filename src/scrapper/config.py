"""Environment-based configuration using Pydantic Settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/scrapper"

    # Logging
    log_level: str = "INFO"

    # HTTP fetch
    fetch_timeout: int = 30
    connect_timeout: int = 10
    request_delay: float = 2.0  # seconds between requests (gentle scraping)

    # Worker
    worker_poll_interval: int = 5
    task_batch_size: int = 10
    max_task_attempts: int = 3

    # Bright Data (optional)
    brightdata_proxy_url: str | None = None
    brightdata_api_key: str | None = None

    # Claude API (optional, for LLM fallback)
    claude_api_key: str | None = None

    # Yandex Maps API (optional, for discovery)
    yandex_api_key: str | None = None

    # 2GIS API (optional, for discovery)
    twogis_api_key: str | None = None

    # Web UI auth
    app_username: str = "admin"
    app_password: str = "changeme"

    # Data paths
    raw_data_dir: Path = Path("data/raw")
    export_dir: Path = Path("data/exports")

    def ensure_dirs(self) -> None:
        """Create data directories if they don't exist."""
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self.export_dir.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings singleton."""
    settings = Settings()
    settings.ensure_dirs()
    return settings
