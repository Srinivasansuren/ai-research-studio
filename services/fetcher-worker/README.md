# Fetcher Worker (Phase IV)

Cloud Run service responsible for deterministic URL fetching and text normalization.

## Responsibilities
- Fetch raw HTML (streamed)
- Deterministic text cleaning
- No LLM usage
- No Firestore access
- Writes evidence snapshots to GCS only

## Endpoints
- GET /healthz
- POST /pubsub/push (Pub/Sub push target)

## Env Vars
- EVIDENCE_BUCKET (required)
