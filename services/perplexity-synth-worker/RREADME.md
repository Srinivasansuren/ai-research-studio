# perplexity-synth-worker (Phase 6)

Pub/Sub push → consumes evidence snapshots (no browsing) → calls Perplexity for synthesis only →
writes NormalizedEvidencePack to GCS (immutable) → updates Firestore job state.

Endpoints:
- GET /healthz
- POST /pubsub/perplexity-synth
