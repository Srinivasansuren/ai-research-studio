Phase IV — Fetcher + Pipeline Coordinator (ONLY)

This diagram shows only what exists in Phase IV.

┌──────────────────────────────┐
│          USER / UI           │
│  (Question, Draft, Prompt)   │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│     ORCHESTRATOR API         │
│  (FastAPI on Cloud Run)      │
│                              │
│  /chat  → Firestore Memory   │  ← (UNCHANGED, FROZEN)
│                              │
│  PipelineRunner (NEW)        │
│  -------------------------   │
│  - validate URLs             │
│  - create request_id         │
│  - publish Pub/Sub messages  │
│  - NO storage                │
│  - NO LLMs                   │
│  - NO Firestore              │
└──────────────┬───────────────┘
               │  Pub/Sub publish
               ▼
┌──────────────────────────────┐
│        PUB / SUB              │
│  Topic: fetch-requests        │
│  (async, at-least-once)       │
└──────────────┬───────────────┘
               │ push delivery
               ▼
┌──────────────────────────────┐
│      FETCHER WORKER           │
│  (Cloud Run service)          │
│                              │
│  - download raw HTML          │
│  - stream, no silent trunc   │
│  - deterministic cleaning    │
│  - compute hashes             │
│  - NO LLMs                    │
│  - NO Firestore               │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│      GCS EVIDENCE BUCKET      │
│  evidence/v1/fetch/...        │
│                              │
│  raw.html                     │
│  clean.txt                    │
│  meta.json                    │
│  done.json                    │
└──────────────────────────────┘

Phase IV Trust Boundaries
[Firestore]  ← only Orchestrator (/chat)
[Pub/Sub]    ← orchestration only
[GCS]        ← evidence only
[LLMs]       ← NOT PRESENT

Combined Architecture — Phase I + II + III + IV

This diagram shows everything that exists today, nothing more.

┌────────────────────────────────────────────────────────┐
│                        USER / UI                        │
│         (chat, question, draft, hypothesis)             │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│                 ORCHESTRATOR API                        │
│           FastAPI • Cloud Run                           │
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │ /chat                                            │ │
│  │  - deterministic message seq                     │ │
│  │  - transactions                                  │ │
│  │  - rehydration                                    │ │
│  │  - memory lifecycle                               │ │
│  │                                                  │ │
│  │  🔒 Phase III FROZEN                               │ │
│  └───────────────┬──────────────────────────────────┘ │
│                  │ Firestore read/write                │
│                  ▼                                     │
│     ┌────────────────────────────────────────────┐    │
│     │            FIRESTORE (Native)               │    │
│     │  tenants / users / conversations / messages │    │
│     │  STRICTLY MEMORY ONLY                       │    │
│     └────────────────────────────────────────────┘    │
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │ PipelineRunner (Phase IV)                        │ │
│  │  - coordination only                             │ │
│  │  - Pub/Sub publish                               │ │
│  │  - NO Firestore                                  │ │
│  │  - NO GCS writes                                 │ │
│  │  - NO LLMs                                       │ │
│  └───────────────┬──────────────────────────────────┘ │
└──────────────────┼────────────────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────────────────┐
│                     PUB / SUB                           │
│   Topic: ars-fetch-requests                             │
│   Async, retry-safe                                     │
└───────────────────┬────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────────────────┐
│                 FETCHER WORKER                          │
│               Cloud Run Service                         │
│                                                        │
│  - fetch raw HTML (streamed)                            │
│  - deterministic cleaning                              │
│  - NO truncation without metadata                      │
│  - NO Firestore                                        │
│  - NO LLMs                                             │
└───────────────────┬────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────────────────┐
│                 GCS EVIDENCE                            │
│    evidence/v1/fetch/YYYY/MM/DD/HH/REQ-ID/              │
│                                                        │
│    raw.html                                             │
│    clean.txt                                            │
│    meta.json                                            │
│    done.json                                            │
└────────────────────────────────────────────────────────┘

########ALL CODE THAT WAS ADDED ###########################
############################################################
(base) MacBook-Pro-2:dev lavanyaasurendar$ terraform apply
╷
│ Error: Module not installed
│ 
│   on main.tf line 74:
│   74: module "fetcher_pubsub" {
│ 
│ This module is not yet installed. Run "terraform init" to install all modules
│ required by this configuration.
base) MacBook-Pro-2:dev lavanyaasurendar$ terraform apply
╷
│ Error: Unsupported attribute
│ 
│   on main.tf line 81, in module "fetcher_pubsub":
│   81:   orchestrator_service_account_email = module.service_accounts.orchestrator_api_sa_email
│     ├────────────────
│     │ module.service_accounts is a object
│ 
│ This object does not have an attribute named "orchestrator_api_sa_email".
(base) MacBook-Pro-2:ai-research-studio lavanyaasurendar$ sed -n '1,200p' infra/modules/service_accounts/outputs.tf
output "orchestrator_sa_email" { value = google_service_account.orchestrator.email }
output "fetcher_sa_email"      { value = google_service_account.fetcher.email }
output "synth_sa_email"        { value = google_service_account.synth.email }
output "debate_sa_email"       { value = google_service_account.debate.email }
output "artifact_sa_email"     { value = google_service_account.artifact.email }
Walk you through the fetcher-worker deploy step-by-step

#######MAJOR ISSUES AND HOW IT GOT RESOLVED ##################
###############################################################

Phase IV Objective (Original Intent)

Phase IV was defined as:

Asynchronous evidence acquisition layer

Orchestrator publishes fetch requests → Pub/Sub → Fetcher Worker pulls, cleans, and stores evidence in GCS.

Key design principles:

No direct service-to-service HTTP calls

Deterministic, replayable jobs

Pub/Sub as the only async boundary

Fetcher is stateless and idempotent

Evidence stored with stable prefixes (request_id, timestamp)

2️⃣ Architecture Implemented in Phase IV
Components Added / Activated
A. Fetcher Worker (Cloud Run)

FastAPI application

Endpoints:

GET /healthz

POST /pubsub/push

Responsibilities:

Decode Pub/Sub push payload

Fetch URL with size + timeout limits

Clean HTML → text

Write:

raw.html

clean.txt

meta.json

done.json

Store in GCS evidence bucket

B. Pub/Sub Push Wiring

Topic: ars-fetch-requests-<env>

Push subscription:

Endpoint: https://fetcher-worker…/pubsub/push

Auth: OIDC

Service account: pubsub-push-invoker-<env>

IAM:

roles/run.invoker granted to push SA on fetcher service

C. Terraform Modules Used

modules/pubsub

modules/fetcher_pubsub

modules/iam

modules/storage

modules/service_accounts

Terraform variables added:

fetcher_worker_url = "https://fetcher-worker-<hash>-uc.a.run.app"

3️⃣ What Worked (Confirmed)
✅ Fetcher Worker (Eventually)

/openapi.json correctly exposed routes

/healthz returned JSON once properly deployed

Pub/Sub push endpoint reachable

GCS writes succeeded

Evidence written with correct prefixes

✅ Terraform Pub/Sub Wiring

Push subscription created correctly

OIDC token configured correctly

IAM bindings correct

No Terraform redesign required

4️⃣ Major Failures & Root Causes
❌ Error 1: Container failed to start (early Phase IV)

Symptoms

Cloud Run revision fails

Startup probe fails on port 8080

Errors:

failed to resolve binary path: error finding executable "gunicorn"
failed to resolve binary path: error finding executable "python"


Root Cause

Using Buildpacks without specifying a correct start command

Cloud Run Buildpack did not auto-detect ASGI startup

gunicorn existed in requirements but was not wired correctly

Fix

Explicit Gunicorn invocation

Let Buildpack manage Python runtime

Ensure app binds to $PORT

❌ Error 2: FastAPI routes returning HTML 404 instead of JSON

Symptoms

/healthz returns Google HTML 404 page

/openapi.json sometimes works, sometimes fails

curl / returns:

{"detail":"Not Found"}


Root Cause

App was running, but:

Wrong Gunicorn worker type

ASGI app being treated as WSGI

Gunicorn sync worker cannot serve FastAPI directly

Evidence in Logs

TypeError: FastAPI.__call__() missing 1 required positional argument: 'send'
Using worker: sync


Fix

Use ASGI worker:

gunicorn main:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:$PORT \
  --workers 1


After redeploy:

/openapi.json works

/healthz returns JSON

No HTML 404s

❌ Error 3: EVIDENCE_BUCKET missing during local import

Symptoms

KeyError: 'EVIDENCE_BUCKET'


Root Cause

create_app() accessed env var at import time

Local testing didn’t inject Cloud Run env vars

Fix

Move env var access inside request handler

Or use .get() with validation

bucket = os.environ.get("EVIDENCE_BUCKET")
if not bucket:
    raise RuntimeError("EVIDENCE_BUCKET env var is required")

❌ Error 4: Auth confusion when testing with curl

Symptoms

curl $URL/healthz → HTML 404

gcloud auth print-identity-token --audiences=... fails:

Invalid account type for --audiences


Root Cause

User credentials ≠ service account credentials

Audience-bound tokens require SA impersonation

Cloud Run auth behavior confused with routing errors

Resolution

Temporarily allow allUsers invoker for debugging

Confirm route correctness before tightening IAM

Recognized that auth was not the root issue

❌ Error 5: Orchestrator /chat returning 500

Symptoms

/chat returns 500

/openapi.json intermittently 500

Stack trace shows Pub/Sub import failure

Error

ImportError: cannot import name 'pubsub_v1' from 'google.cloud'


Root Cause

google-cloud-pubsub missing from orchestrator requirements

Buildpack Python 3.13 environment did not include it

Import path correct, dependency missing

Fix

google-cloud-pubsub==2.x.x


added to orchestrator-api/requirements.txt

5️⃣ Key Lessons from Phase IV
1. Gunicorn defaults are dangerous for FastAPI

sync worker = WSGI

FastAPI = ASGI

Must explicitly set UvicornWorker

2. Cloud Run HTML 404 ≠ FastAPI 404

HTML page → request never reached app

JSON { "detail": "Not Found" } → FastAPI handled it

3. Buildpacks hide a lot

Missing dependencies don’t fail build

They fail at runtime

Logs are mandatory

4. Auth errors often mask routing errors

Always verify /openapi.json first

Then /healthz

Only then debug IAM

6️⃣ Phase IV Final State (As of Now)
✅ Fetcher Worker

Fully functional

Pub/Sub push wired

GCS evidence writing works

Health endpoint confirmed

⚠️ Orchestrator API

Core API works

/openapi.json works

/chat Pub/Sub publish path was broken but identified

Missing dependency fixed conceptually

Needs clean redeploy with corrected Gunicorn worker + deps

7️⃣ What Phase IV Achieved

✔ Async boundary established
✔ Deterministic fetch jobs
✔ Evidence persistence pipeline live
✔ Terraform wiring validated
✔ Cloud Run operational patterns learned (hard way)