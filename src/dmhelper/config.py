from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    anthropic_api_key: SecretStr = Field(..., alias="ANTHROPIC_API_KEY")
    kanka_api_token: SecretStr = Field(..., alias="KANKA_API_TOKEN")
    kanka_campaign_id: int = Field(..., alias="KANKA_CAMPAIGN_ID")

    # Optional: used ONLY to upload Agents-SDK traces to your OpenAI
    # dashboard. Model calls still route to Claude via LiteLLM.
    openai_api_key: SecretStr | None = Field(
        default=None, alias="OPENAI_API_KEY"
    )
    tracing_enabled: bool = Field(True, alias="DMHELPER_TRACING_ENABLED")

    orchestrator_model: str = Field(
        "anthropic/claude-opus-4-8", alias="DMHELPER_ORCHESTRATOR_MODEL"
    )
    writer_model: str = Field(
        "anthropic/claude-opus-4-8", alias="DMHELPER_WRITER_MODEL"
    )
    judge_model: str = Field(
        "anthropic/claude-sonnet-4-6", alias="DMHELPER_JUDGE_MODEL"
    )
    web_model: str = Field("claude-sonnet-4-6", alias="DMHELPER_WEB_MODEL")
    judge_enabled: bool = Field(True, alias="DMHELPER_JUDGE_ENABLED")
    data_dir: Path = Field(Path("data"), alias="DMHELPER_DATA_DIR")

    @property
    def lore_dir(self) -> Path:
        return self.data_dir / "lore"

    @property
    def alexya_lore_dir(self) -> Path:
        """World-of-Alaxya lore (Deities, History, Geography, Seven Espada)."""
        return self.data_dir / "lore" / "alaxya"

    @property
    def group_lore_dir(self) -> Path:
        """Per-play-group backstory / info files."""
        return self.data_dir / "lore" / "player groups"

    @property
    def memory_dir(self) -> Path:
        return self.data_dir / "memory"

    @property
    def sessions_db_path(self) -> Path:
        return self.data_dir / "sessions.db"

    @property
    def store_db_path(self) -> Path:
        return self.data_dir / "store.db"

    @property
    def prompts_dir(self) -> Path:
        return Path("prompts")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
