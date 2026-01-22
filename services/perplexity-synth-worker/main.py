import os
import logging

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.logging import setup_logging
from app.routes.health import router as health_router
from app.routes.pubsub_synth import router as synth_router

# -------------------------------------------------------------------
# Logging
# -------------------------------------------------------------------
setup_logging()
logger = logging.getLogger("perplexity-synth-worker")

# -------------------------------------------------------------------
# FastAPI app
# -------------------------------------------------------------------
app = FastAPI(
    title="perplexity-synth-worker",
    version=os.getenv("PIPELINE_VERSION", "dev"),
)

# -------------------------------------------------------------------
# Routes
# -------------------------------------------------------------------
app.include_router(health_router)
app.include_router(synth_router)


@app.get("/")
def root():
    return {"ok": True, "service": "perplexity-synth-worker"}


# -------------------------------------------------------------------
# Startup hook (PRODUCTION-SAFE)
# -------------------------------------------------------------------
@app.on_event("startup")
def startup_check():
    """
    Runs after uvicorn boot, before accepting traffic.

    Purpose:
    - Load and validate configuration
    - Fail fast with clear logs if misconfigured
    - Avoid import-time crashes in Cloud Run
    """
    try:
        from app.config import get_settings  # ✅ import accessor, not singleton
        settings = get_settings()

        logger.info("Configuration loaded successfully")
        logger.info("Pipeline version: %s", settings.PIPELINE_VERSION)
        logger.info("Perplexity model: %s", settings.PERPLEXITY_MODEL)
        logger.info("Evidence bucket: %s", settings.EVIDENCE_BUCKET)

        # NEVER log secrets
        logger.info(
            "Perplexity API key present: %s",
            bool(settings.PERPLEXITY_API_KEY),
        )

    except Exception:
        # logger.exception preserves full traceback in Cloud Run logs
        logger.exception("Startup configuration error")
        # IMPORTANT: raise so Cloud Run marks revision unhealthy
        raise
