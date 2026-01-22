# main.py
import logging
from fastapi import FastAPI

from app.config import get_settings
from app.routes.health import router as health_router
from app.routes.pubsub_jobs import router as jobs_router
from app.routes.pubsub_evidence import router as evidence_router


logger = logging.getLogger("pipeline-runner")

app = FastAPI(title="pipeline-runner")


@app.on_event("startup")
def startup() -> None:
    """
    Validate and load configuration once per container instance.
    Fails fast if configuration is invalid, but AFTER imports succeed.
    """
    settings = get_settings()
    app.state.settings = settings

    logger.info(
        "pipeline-runner startup complete | project_id=%s | pipeline_version=%s",
        settings.project_id,
        settings.runner_pipeline_version,
    )


# --------------------
# Routes
# --------------------
app.include_router(health_router)
app.include_router(jobs_router)
app.include_router(evidence_router)

############ TEMP DEBUG END POINT ######################
########################################################
@app.get("/__debug/routes")
def debug_routes():
    return [
        {
            "path": r.path,
            "methods": list(r.methods),
            "name": r.name,
        }
        for r in app.router.routes
    ]
