"""Application configuration via environment variables.

Single source of truth for all configuration values. Uses pydantic-settings
to load from environment variables with sensible defaults for development.
"""

from __future__ import annotations

from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All application configuration, loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="TRACKER_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- Application ---
    app_name: str = "Shipment Tracker"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    # --- Database ---
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "shipment_tracker"
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_min_pool_size: int = 2
    db_max_pool_size: int = 10

    @property
    def database_url(self) -> str:
        """Build the PostgreSQL connection string."""
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    # --- AIS Integration ---
    ais_provider: str = "mock"  # "marinetraffic" or "mock"
    ais_api_key: str = ""
    ais_base_url: str = "https://services.marinetraffic.com/api/exportvessel/v:8"
    ais_poll_interval_seconds: int = 300  # 5 minutes

    # --- Gmail Integration ---
    gmail_credentials_path: str = "credentials.json"
    gmail_token_path: str = "token.json"
    gmail_poll_interval_seconds: int = 120  # 2 minutes
    gmail_query_filter: str = "subject:(charcoal OR shipment OR vessel OR B/L OR charter)"

    # --- Alert Engine ---
    alert_check_interval_seconds: int = 600  # 10 minutes
    route_deviation_threshold_nm: float = 50.0
    old_alert_cleanup_days: int = 30

    # --- AI / Anthropic ---
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-5-20250514"

    # --- Deepgram (Transcription) ---
    deepgram_api_key: str = ""

    # --- Google Calendar Sync ---
    calendar_sync_interval_seconds: int = 300  # 5 minutes

    # --- Auth / JWT ---
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # --- CORS ---
    cors_origins: list[str] = ["*"]

    # --- Paths ---
    @property
    def schema_path(self) -> Path:
        """Path to the SQL schema file."""
        return Path(__file__).parent / "models" / "schema.sql"

    @property
    def seed_path(self) -> Path:
        """Path to the SQL seed file."""
        return Path(__file__).parent / "models" / "seed.sql"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
