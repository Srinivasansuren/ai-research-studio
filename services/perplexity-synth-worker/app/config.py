# app/config.py
from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central configuration for the service.
    Pydantic v2 Settings via pydantic-settings.
    """

    model_config = SettingsConfigDict(
        env_prefix="",          # no prefix unless you want one
        case_sensitive=False,
        extra="ignore",         # ignore unexpected env vars in Cloud Run
    )

    # Core
    PROJECT_ID: str = Field(..., description="GCP project id")
    REGION: str = Field(..., description="GCP region")
    PIPELINE_VERSION: str = Field(..., description="Pipeline version tag")

    # Perplexity
    PERPLEXITY_MODEL: str = Field("sonar-pro", description="Perplexity model name")
    PERPLEXITY_API_KEY: str = Field(..., description="Perplexity API key")

    # Storage
    EVIDENCE_BUCKET: str = Field(..., description="GCS bucket for evidence outputs")

    # Optional runtime knobs
    LOG_LEVEL: str = Field("INFO", description="Logging level")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Cached settings loader. Fails fast with a clear error if misconfigured.
    """
    try:
        return Settings()
    except ValidationError as e:
        # Keep this extremely explicit. Cloud Run logs will show missing env vars.
        missing = []
        for err in e.errors():
            if err.get("type") == "missing":
                loc = err.get("loc")
                if loc:
                    missing.append(str(loc[-1]))
        missing_str = ", ".join(missing) if missing else "(see validation errors)"

        raise RuntimeError(
            "Configuration validation failed. "
            f"Missing/invalid env vars: {missing_str}. "
            "Check Cloud Run service env vars and secrets."
        ) from e
