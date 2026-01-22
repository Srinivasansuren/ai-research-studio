infra/
├── bootstrap/
│   ├── main.tf
│   ├── outputs.tf
│   ├── terraform.tfstate
│   ├── terraform.tfstate.backup
│   └── variables.tf
│
├── envs/
│   └── dev/
│       ├── .terraform/
│       ├── terraform.lock.hcl
│       ├── backend.tf
│       ├── dev.tfvars
│       ├── main.tf
│       ├── outputs.tf
│       └── variables.tf
│
├── modules/
│   ├── fetcher_pubsub/
│   │   ├── main.tf
│   │   ├── outputs.tf
│   │   └── variables.tf
│   │
│   ├── firestore/
│   │   ├── main.tf
│   │   ├── outputs.tf
│   │   └── variables.tf
│   │
│   ├── iam/
│   │   ├── main.tf
│   │   ├── outputs.tf
│   │   └── variables.tf
│   │
│   ├── pipeline_runner/
│   │   ├── main.tf
│   │   ├── outputs.tf
│   │   └── variables.tf
│   │
│   ├── project_services/
│   │   ├── main.tf
│   │   └── variables.tf
│   │
│   ├── pubsub/
│   │   ├── main.tf
│   │   ├── outputs.tf
│   │   └── variables.tf
│   │
│   ├── service_accounts/
│   │   ├── main.tf
│   │   ├── outputs.tf
│   │   └── variables.tf
│   │
│   └── storage/
│       ├── main.tf
│       ├── outputs.tf
│       └── variables.tf

Services code: 

services/
├── fetcher-worker/
│   ├── __pycache__/
│   ├── .venv/
│   ├── app/
│   │   ├── __pycache__/
│   │   ├── __init__.py
│   │   ├── clean.py
│   │   ├── contracts.py
│   │   ├── fetch.py
│   │   ├── gcs.py
│   │   ├── server.py
│   │   └── util.py
│   ├── main.py
│   ├── Procfile
│   ├── README.md
│   ├── requirements.txt
│   └── runtime.txt
│
├── orchestrator-api/
│   ├── app/
│   │   ├── memory/
│   │   │   ├── chat_memory.py
│   │   │   └── firestore_client.py
│   │   │
│   │   ├── pipeline/
│   │   │   ├── __pycache__/
│   │   │   ├── __init__.py
│   │   │   ├── contracts.py
│   │   │   ├── ids.py
│   │   │   ├── pubsub_client.py
│   │   │   └── runner.py
│   │   │
│   │   ├── routes/
│   │   │   ├── __pycache__/
│   │   │   ├── chat.py
│   │   │   └── __init__.py
│   │   │
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── README.md
│   │   └── requirements.txt
│
├── pipeline-runner/
│   ├── app/
│   │   ├── contracts/
│   │   │   ├── __init__.py
│   │   │   └── fetcher_contract.py
│   │   │
│   │   ├── external/
│   │   │   ├── __init__.py
│   │   │   └── serpapi.py
│   │   │
│   │   ├── pubsub/
│   │   │   ├── __init__.py
│   │   │   └── publisher.py
│   │   │
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── health.py
│   │   │   ├── pubsub_evidence.py
│   │   │   └── pubsub_jobs.py
│   │   │
│   │   ├── state/
│   │   │   ├── __init__.py
│   │   │   ├── dedupe.py
│   │   │   ├── firestore.py
│   │   │   └── jobs.py
│   │   │
│   │   ├── storage/
│   │   │   ├── __init__.py
│   │   │   └── gcs.py
│   │   │
│   │   ├── config.py
│   │   └── logging.py
│   │
│   ├── Dockerfile
│   ├── main.py
│   ├── Procfile
│   ├── README.md
│   ├── requirements.txt
│   ├── runtime.txt
│   ├── .clear-args
│   ├── .clear-command
│   ├── .region
│   └── .gitignore

# Phase VI integrated flow

(Phase 5 ends)
Fetcher writes snapshots to GCS
   ↓
pipeline-runner receives evidence finalize event (existing)
   ↓
Firestore job state: EVIDENCE_READY (transactional)
   ↓
pipeline-runner publishes Pub/Sub message: perplexity-synth-requests (NEW topic)
   ↓
perplexity-synth-worker receives push (NEW service)
   ↓
Firestore: SYNTHESIS_IN_PROGRESS (transactional, idempotent)
   ↓
Worker loads snapshot text ONLY from request (or from GCS if you choose pointer mode)
   ↓
Perplexity API call (NO browsing; snapshots-only prompt)
   ↓
Write NormalizedEvidencePack to GCS (immutable)
   ↓
Firestore: SYNTHESIS_COMPLETE + pointer to pack (transactional)
   ↓
(Phase 6 stops. Debate begins Phase 7, not here.)

##### Key code to understand everything created ###############