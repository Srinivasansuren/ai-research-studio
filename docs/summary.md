You are helping me continue building a production-grade AI Research Studio on Google Cloud Platform (GCP).
This is a serious engineering project, not a demo.

Proceed like a staff / principal engineer.
Do not redesign completed phases.
Respect all locked architecture and phase boundaries.

Build an AI Research Studio that:

• Accepts a user question, hypothesis, or draft (text, equations, code, PDFs, links)
• Gathers web evidence in a controlled, reproducible way
• Synthesizes evidence
• Runs multi-LLM debate (NO web access during debate)
• Produces aligned, structured output:
– Text (Markdown)
– Equations (LaTeX)
– Code (executable, versioned)
– Charts (reproducible)
• Saves results as reusable artifacts with unique IDs (ART-xxxxx)
• Supports fresh chats that can rehydrate saved artifacts
• Supports text search over past inputs/outputs
• Supports re-running saved analysis code to regenerate charts
• Supports DOCX and PDF export

User Question
↓
SerpAPI (top 50–100 URLs, deterministic, timestamped)
↓
Fetcher Worker (downloads & cleans text)
↓
Perplexity (SEARCH + SYNTHESIS ONLY)
↓
Normalized Evidence Pack (versioned, saved)
↓
Debate LLMs (OpenAI / Claude / Groq / Grok)
↓ (NO WEB ACCESS HERE)
Referee / Alignment Layer
↓
Structured Output Blocks (text / equations / code / charts)

Hard rules:
• Perplexity MUST NOT participate in debate
• Debate LLMs MUST NOT browse the web
• Evidence must be snapshot-based and reproducible
• Memory and pipeline MUST remain separate

🧱 PHASE I — ORCHESTRATOR STUB (COMPLETE, FROZEN)

• FastAPI on Cloud Run
• Endpoints:
– /healthz
– /chat
• Buildpacks (NO Dockerfile)
• No storage, no pipeline, no async

Status: ✅ COMPLETE (FROZEN)

🧱 PHASE II — INFRASTRUCTURE & PLUMBING (COMPLETE, FROZEN)

Terraform-managed infrastructure under infra/

Remote state:
• GCS bucket created in infra/bootstrap

Active env:
• Terraform applied from infra/envs/dev

Resources created:
• Firestore (Native, nam5)
• Pub/Sub:
– Topic: ars-jobs-dev
– Subscription: ars-jobs-sub-dev (PULL, idle, NOT to be reused)
• GCS buckets:
– ars-evidence-ai-research-studio-dev
– ars-artifacts-ai-research-studio-dev
– ars-charts-ai-research-studio-dev
• IAM fully codified

Service Accounts (Terraform-managed):
• orchestrator-api-sa-dev
• fetcher-worker-sa-dev
• artifact-writer-sa-dev
• evidence-synth-sa-dev
• debate-runner-sa-dev

Status: ✅ COMPLETE (FROZEN)

🧱 PHASE III — DETERMINISTIC CHAT MEMORY (COMPLETE, FROZEN)

• Firestore-backed chat memory
• Deterministic sequencing via transactions
• Conversation lifecycle + rehydration
• Orchestrator-only read/write
• Pipeline-agnostic memory design

/chat flow:
get_or_create_conversation()
rehydrate()
append(user message)
(pipeline placeholder)
append(assistant message)
attach_artifacts()

Guarantees:
• Single writer
• Full replayability
• Sequence integrity validated

Status: ✅ COMPLETE (FROZEN)

🎯 Goal:
Lay the foundation of the evidence pipeline without running SerpAPI, Perplexity, debate, or artifact generation.

Phase IV introduces ONLY:

Fetcher Worker (Cloud Run service)

Pipeline Runner abstraction (orchestrator-side)

❌ No Firestore access
❌ No LLM calls
❌ No SerpAPI yet
❌ No reuse of ars-jobs-dev

🔹 Fetcher Worker

• Cloud Run service: fetcher-worker (NOT YET DEPLOYED)
• Triggered via Pub/Sub PUSH
• Input: explicit URLs only (from orchestrator via Pub/Sub)
• Fetches raw HTML (streamed, no silent truncation)
• Deterministic cleaning
• Writes ONLY to GCS evidence bucket

Evidence layout:
evidence/v1/fetch/YYYY/MM/DD/HH/<request_id>/
– raw.html
– clean.txt
– meta.json
– done.json

Service account:
• fetcher-worker-sa-dev
• Has roles/storage.objectAdmin on evidence bucket ONLY

🔹 Pipeline Runner (orchestrator-side)

• Pure coordination boundary
• Publishes fetch jobs to Pub/Sub
• Does NOT touch Firestore
• Does NOT write to GCS
• Does NOT call LLMs
• Does NOT add new /chat behavior

Exists as code only (may be unused until Phase V).

🔹 Pub/Sub (Phase IV additions)

DO NOT reuse:
• ars-jobs-dev

NEW (Phase IV):
• Topic: ars-fetch-requests-dev
• Subscription: ars-fetch-requests-push-dev (PUSH)
• Auth: OIDC push using a dedicated SA

New service account:
• pubsub-push-invoker-dev
• Has roles/run.invoker on fetcher-worker ONLY

🔹 Cloud Run Auth Model

• orchestrator-api is PUBLIC (allUsers invoker)
• fetcher-worker will be PRIVATE (IAM only)
• Pub/Sub push uses OIDC (no unauthenticated endpoints)

• Firestore memory is frozen and authoritative
• Pipeline side effects MUST cross Pub/Sub
• Fetcher never discovers links
• Orchestrator never fetches content
• Evidence is immutable and replayable
• Phase IV must remain forward-compatible with Phase V+

Proceed ONLY with Phase IV unless explicitly instructed otherwise.

PART 2 — UPDATED CODE (SAME STRUCTURE, NO NEW FOLDERS)

You explicitly said:

“do not modify the following folder you suggested earlier … and give me the updated code”

So I will:

✅ KEEP THE EXACT STRUCTURE YOU LISTED
✅ ONLY UPDATE CONTENT to match your real infra
❌ NO restructuring
❌ NO new folders

Below is what changes and what does not.

✅ What stays exactly the same (structure)
ai-research-studio/
  orchestrator-api/
    app/
      pipeline/
        __init__.py
        contracts.py
        runner.py
        pubsub_client.py
        ids.py
  fetcher-worker/
    app/
      __init__.py
      server.py
      fetch.py
      gcs.py
      clean.py
      contracts.py
      util.py
    main.py
    requirements.txt
    Procfile
    README.md
  terraform/
    phase4_fetcher.tf
    variables_phase4.tf
    outputs_phase4.tf


⚠️ Important clarification
The terraform/ folder here should be treated as “Phase IV Terraform snippets to be merged into your existing infra modules”, NOT a new Terraform root.

This respects everything we established earlier.