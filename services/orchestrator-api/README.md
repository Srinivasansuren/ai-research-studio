# orchestrator-api

Phase 1 FastAPI service for Cloud Run source-based deploy.

Endpoints:
- GET  /healthz
- POST /chat  (stubbed, no LLMs, no web, no storage yet)

Deploy:
- Uses `gcloud run deploy --source`
- No Terraform in Phase 1
- No Dockerfiles
