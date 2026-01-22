
Phase 1: Repo scaffolding + first Cloud Run service (`orchestrator-api`).

This repo will evolve through locked phases:
- Phase 1: Cloud Run source deploy + FastAPI stub
- Phase 2+: Terraform infra, Firestore, Pub/Sub, GCS, etc.

## Services
- `services/orchestrator-api`: API entrypoint (chat orchestration) — currently stubbed.

# Phase 1 — Cloud Run Source Deploy (FastAPI)  
**AI Research Studio — GCP**

This document records the **exact steps, fixes, IAM changes, and commands** used to successfully complete **Phase 1** of the AI Research Studio project.

Phase 1 goal:  
> Prove that a FastAPI service can be deployed to **Cloud Run** on **GCP** using **source-based deploy (Buildpacks)** — no Dockerfile, no Terraform.

---

## 0. Preconditions

- GCP Project: `ai-research-studio`
- Region: `us-central1`
- OS: macOS (Intel)
- Deployment method: `gcloud run deploy --source`
- Repo is the **source of truth**
- No Terraform yet
- No CI/CD yet

---

## 1. Repository Structure (Phase 1)

ai-research-studio/
├── README.md
├── .gitignore
└── services/
└── orchestrator-api/
├── main.py
├── requirements.txt
├── runtime.txt
├── app.yaml

python
Copy code

---

## 2. FastAPI Application (`main.py`)

```python
from fastapi import FastAPI
from pydantic import BaseModel
import time, uuid

app = FastAPI(title="orchestrator-api", version="0.1.0-phase1")

class ChatRequest(BaseModel):
    message: str

@app.get("/healthz")
def healthz():
    return {
        "ok": True,
        "service": "orchestrator-api",
        "time": int(time.time()),
    }

@app.post("/chat")
def chat(req: ChatRequest):
    return {
        "request_id": f"REQ-{uuid.uuid4().hex[:12]}",
        "output": "Phase 1 stub response",
        "echo": req.message,
    }
3. Python Dependencies (requirements.txt)
txt
Copy code
fastapi==0.115.6
uvicorn[standard]==0.32.1
pydantic==2.10.3
Important notes

uvicorn is REQUIRED for Cloud Run buildpacks

gunicorn is NOT used by Cloud Run source deploy

4. Runtime Declaration (runtime.txt)
txt
Copy code
python311
This makes Python version explicit and deterministic.

5. Explicit Entry Point (app.yaml)
Cloud Run does not read Procfile.
FastAPI requires an explicit startup command.

yaml
Copy code
runtime: python311
entrypoint: uvicorn main:app --host 0.0.0.0 --port $PORT
This file is the key fix that allowed Cloud Run buildpacks to start the app.

6. GCP Configuration
Set project and region
bash
Copy code
gcloud config set project ai-research-studio
gcloud config set run/region us-central1
Fix ADC quota mismatch
bash
Copy code
gcloud auth application-default set-quota-project ai-research-studio
7. Enable Required APIs
bash
Copy code
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com
8. Artifact Registry Setup
Cloud Run does not auto-create repositories for explicit builds.

Create Docker repository
bash
Copy code
gcloud artifacts repositories create cloud-run \
  --repository-format=docker \
  --location=us-central1 \
  --description="Docker repository for Cloud Run services"
Verify:

bash
Copy code
gcloud artifacts repositories list --location=us-central1
9. Critical IAM Fixes (Org-Managed Project)
Because this is an organization-managed GCP project, several default roles were missing.

9.1 Grant Cloud Build logging permission
bash
Copy code
gcloud projects add-iam-policy-binding ai-research-studio \
  --member="serviceAccount:388411931994-compute@developer.gserviceaccount.com" \
  --role="roles/logging.logWriter"
9.2 Grant Artifact Registry write permission
bash
Copy code
gcloud projects add-iam-policy-binding ai-research-studio \
  --member="serviceAccount:388411931994-compute@developer.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"
These two roles were mandatory to unblock Cloud Build and image push.

10. Build Image with Buildpacks (Explicit)
We bypassed the brittle gcloud run deploy --source glue by running Buildpacks explicitly.

bash
Copy code
gcloud builds submit \
  services/orchestrator-api \
  --pack image=us-central1-docker.pkg.dev/ai-research-studio/cloud-run/orchestrator-api
Result:

makefile
Copy code
STATUS: SUCCESS
11. Deploy Image to Cloud Run
bash
Copy code
gcloud run deploy orchestrator-api \
  --image us-central1-docker.pkg.dev/ai-research-studio/cloud-run/orchestrator-api \
  --region us-central1 \
  --allow-unauthenticated
12. Verification
List services
bash
Copy code
gcloud run services list --region us-central1
Output:

Copy code
✔ orchestrator-api  us-central1
✔ hello-test        us-central1
Health check
bash
Copy code
curl https://orchestrator-api-388411931994.us-central1.run.app/healthz
Chat stub
bash
Copy code
curl https://orchestrator-api-388411931994.us-central1.run.app/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Phase 1 complete"}'
13. Lessons Learned (Important)
Cloud Run ignores Procfile

FastAPI requires explicit entrypoint

Org-managed projects strip default IAM roles

FAILED_PRECONDITION errors often mean missing IAM on build service accounts

Explicit Cloud Build → Image → Cloud Run is more reliable than --source

14. Phase 1 Outcome
Phase 1 is COMPLETE

✔ FastAPI service live
✔ Cloud Run working
✔ Buildpacks working
✔ Artifact Registry wired
✔ No Dockerfile
✔ Production-grade foundation

