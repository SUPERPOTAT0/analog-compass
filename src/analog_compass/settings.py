"""Environment-driven settings. No secrets in code; values come from env / .env."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    data_mode: str = "synthetic"  # synthetic | real
    data_bundle_uri: str = "data/synthetic"
    data_version: str = "synthetic-0.1.0"

    engine_n_draws: int = 512
    engine_seed_salt: str = "analog-compass"

    anthropic_api_key: str | None = None
    analog_agent_model: str | None = None
    analog_agent_max_tool_iters: int = 8

    allowed_origins: str = "http://localhost:3000"

    @property
    def config_dir(self) -> Path:
        return REPO_ROOT / "config"

    @property
    def bundle_dir(self) -> Path:
        p = Path(self.data_bundle_uri)
        return p if p.is_absolute() else REPO_ROOT / p

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
