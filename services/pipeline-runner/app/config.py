# app/config.py
from functools import lru_cache
from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ======================
    # GCP
    # ======================
    project_id: str = Field(
        ...,
        validation_alias=AliasChoices(
            "PROJECT_ID",
            "GOOGLE_CLOUD_PROJECT",
            "GCP_PROJECT",
            "ARS_PROJECT_ID",
        ),
        description="GCP project id",
    )

    # ======================
    # Firestore
    # ======================
    firestore_database: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "FIRESTORE_DATABASE",
            "ARS_FIRESTORE_DATABASE",
        ),
    )

    # ======================
    # Pub/Sub
    # ======================
    fetch_requests_topic: str = Field(
        ...,
        validation_alias=AliasChoices(
            "FETCH_REQUESTS_TOPIC",
            "ARS_FETCH_REQUESTS_TOPIC",
        ),
    )

    debate_requests_topic: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "DEBATE_REQUESTS_TOPIC",
            "ARS_DEBATE_REQUESTS_TOPIC",
        ),
    )

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    # Phase VI — Perplexity Synthesis (NEW)
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    perplexity_synth_topic: str = Field(
        ...,
        validation_alias=AliasChoices(
            "PERPLEXITY_SYNTH_TOPIC",
            "ARS_PERPLEXITY_SYNTH_TOPIC",
        ),
        description="Pub/Sub topic for Phase VI Perplexity synthesis",
    )

    perplexity_prompt_version: str = Field(
        default="perplexity_synth_prompt.v1",
        validation_alias=AliasChoices(
            "PERPLEXITY_PROMPT_VERSION",
            "ARS_PERPLEXITY_PROMPT_VERSION",
        ),
        description="Versioned prompt id for Perplexity synthesis",
    )

    # ======================
    # Evidence storage
    # ======================
    evidence_bucket: str = Field(
        ...,
        validation_alias=AliasChoices(
            "EVIDENCE_BUCKET",
            "ARS_EVIDENCE_BUCKET",
        ),
    )

    evidence_object_prefix: str = Field(
        default="tenants/",
        validation_alias=AliasChoices(
            "EVIDENCE_OBJECT_PREFIX",
            "ARS_EVIDENCE_OBJECT_PREFIX",
        ),
    )

    # ======================
    # SerpAPI
    # ======================
    serpapi_api_key: str = Field(
        ...,
        validation_alias=AliasChoices(
            "SERPAPI_API_KEY",
            "ARS_SERPAPI_API_KEY",
        ),
    )

    serpapi_engine: str = Field(default="google")
    serpapi_gl: str = Field(default="us")
    serpapi_hl: str = Field(default="en")
    serpapi_top_n: int = Field(default=10)

    # ======================
    # Runtime behavior
    # ======================
    runner_pipeline_version: str = Field(default="v1")
    max_urls_hard_cap: int = Field(default=25)

    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Lazy, cached settings loader.
    Validation happens once per container, not at import time.
    """
    return Settings()
