########## PHASE II ####################################
########################################################

# Phase 2 — Terraform Infrastructure (Production Foundation)

This document records **all infrastructure created in Phase 2** of the  
**AI Research Studio on Google Cloud Platform**.

Phase 2 establishes a **deterministic, auditable, production-grade foundation**
on which all later phases depend.

No application logic, no LLM logic, and no architectural redesign occurred in this phase.

---

## Phase 2 Goals (Locked)

Phase 2 is responsible for:

- Codifying infrastructure via **Terraform**
- Eliminating manual IAM configuration
- Creating durable, versioned storage
- Creating async job infrastructure
- Creating explicit service identities
- Preparing the platform for later phases

Out of scope:
- No LLM integration
- No fetcher logic
- No UI
- No code execution
- No SerpAPI or Perplexity usage

---

## High-Level Architecture (Phase 2)

┌──────────────────────┐
│ Orchestrator API │
│ (Cloud Run, SA #1) │
└─────────┬────────────┘
│ publishes jobs
▼
┌──────────────────────────────┐
│ Pub/Sub Topic │
│ ars-jobs-dev │
└─────────┬────────────────────┘
│
▼
┌──────────────────────────────┐
│ Pub/Sub Subscription │
│ ars-jobs-sub-dev │
└─────────┬────────────────────┘
│
│ consumed by workers (later phases)
▼
┌─────────────────────────────────────────────┐
│ Workers (Fetcher / Synth / Debate / Artifact)│
│ Each with its own Service Account │
└─────────────────────────────────────────────┘

Persistent Storage:
───────────────────
Firestore (Native) → Chat memory, metadata
GCS (Evidence) → Snapshot-based web evidence
GCS (Artifacts) → ART-xxxxx outputs
GCS (Charts) → Regenerated visual outputs

yaml
Copy code

---

## Terraform Structure

infra/
├── bootstrap/
│ ├── main.tf
│ ├── variables.tf
│ └── outputs.tf
│
├── envs/
│ └── dev/
│ ├── backend.tf
│ ├── main.tf
│ ├── variables.tf
│ └── outputs.tf
│
└── modules/
├── project_services/
├── service_accounts/
├── firestore/
├── pubsub/
├── storage/
└── iam/

yaml
Copy code

---

## Bootstrap Layer (One-Time)

### Purpose
Creates the **Terraform remote state bucket**.

Terraform cannot use a backend bucket that does not already exist.

### Result
- Remote state stored in GCS
- Versioned
- Locked to environment prefix

### Resource Created
ai-research-studio-tfstate

yaml
Copy code

---

## Project Services Module

### Purpose
Enables all required GCP APIs **declaratively**.

### APIs Enabled
- serviceusage.googleapis.com
- iam.googleapis.com
- run.googleapis.com
- artifactregistry.googleapis.com
- cloudbuild.googleapis.com
- secretmanager.googleapis.com
- firestore.googleapis.com
- pubsub.googleapis.com
- storage.googleapis.com
- logging.googleapis.com
- monitoring.googleapis.com

No API enablement is done manually.

---

## Service Accounts Module

### Purpose
Creates **one service account per responsibility**.

This is critical for:
- Least privilege IAM
- Auditability
- Later security reviews

### Service Accounts (Canonical)

orchestrator-api-sa-dev@ai-research-studio.iam.gserviceaccount.com
fetcher-worker-sa-dev@ai-research-studio.iam.gserviceaccount.com
evidence-synth-sa-dev@ai-research-studio.iam.gserviceaccount.com
debate-runner-sa-dev@ai-research-studio.iam.gserviceaccount.com
artifact-writer-sa-dev@ai-research-studio.iam.gserviceaccount.com

yaml
Copy code

Each maps 1:1 to a pipeline stage.

---

## Firestore Module

### Purpose
Provision **Firestore in Native Mode**.

Used for:
- Chat sessions
- Message lineage
- Artifact pointers
- Deterministic rehydration

### Configuration
- Database: `(default)`
- Mode: `FIRESTORE_NATIVE`
- Location: `nam5` (North America)

⚠ Firestore is one-per-project and immutable once created.

---

## Pub/Sub Module

### Purpose
Create the async backbone of the system.

### Resources

Topic:
projects/ai-research-studio/topics/ars-jobs-dev

Subscription:
projects/ai-research-studio/subscriptions/ars-jobs-sub-dev

yaml
Copy code

### Design Notes
- Orchestrator publishes jobs
- Workers subscribe
- Retry policy configured
- DLQ intentionally deferred to later phase

---

## Storage Module (GCS)

### Purpose
Create durable, versioned object storage with **clear semantic separation**.

### Buckets (Canonical)

ars-evidence-ai-research-studio-dev
ars-artifacts-ai-research-studio-dev
ars-charts-ai-research-studio-dev

yaml
Copy code

### Semantics

| Bucket | Purpose |
|------|--------|
| evidence | Immutable snapshots of fetched web content |
| artifacts | Final research outputs (ART-xxxxx) |
| charts | Regenerated charts & visual outputs |

### Properties
- Uniform bucket-level access: **enabled**
- Versioning: **enabled**
- Lifecycle: deletes very old noncurrent versions

---

## IAM Module

### Purpose
Codify **all permissions explicitly**.

No service has project-owner or editor access.

### Firestore IAM
All services receive:
roles/datastore.user

yaml
Copy code

### Pub/Sub IAM
- Orchestrator: `roles/pubsub.publisher`
- Workers: `roles/pubsub.subscriber`

### GCS IAM (Bucket-Scoped)

Evidence bucket:
- Fetcher: objectAdmin
- Orchestrator / Synth / Artifact: objectViewer

Artifacts bucket:
- Artifact writer: objectAdmin
- Orchestrator: objectViewer

Charts bucket:
- Artifact writer: objectAdmin
- Orchestrator: objectViewer

No wildcard project-level storage roles exist.

---

## Phase 2 Outputs (Recorded)

```hcl
buckets = {
  artifacts = "ars-artifacts-ai-research-studio-dev"
  charts    = "ars-charts-ai-research-studio-dev"
  evidence  = "ars-evidence-ai-research-studio-dev"
}

pubsub = {
  topic        = "projects/ai-research-studio/topics/ars-jobs-dev"
  subscription = "projects/ai-research-studio/subscriptions/ars-jobs-sub-dev"
}

service_accounts = {
  orchestrator = "orchestrator-api-sa-dev@ai-research-studio.iam.gserviceaccount.com"
  fetcher      = "fetcher-worker-sa-dev@ai-research-studio.iam.gserviceaccount.com"
  synth        = "evidence-synth-sa-dev@ai-research-studio.iam.gserviceaccount.com"
  debate       = "debate-runner-sa-dev@ai-research-studio.iam.gserviceaccount.com"
  artifact     = "artifact-writer-sa-dev@ai-research-studio.iam.gserviceaccount.com"
}
These names are authoritative and should be treated as stable contracts.

# CODE FOR PHASE II ##########################
Assumptions I’m making for Phase 2 (call these “defaults” you can override)

I’m going to proceed with these sane production defaults unless you tell me otherwise:

One environment for now: dev (we’ll structure Terraform so adding prod is trivial).

Region: us-central1 (your Cloud Run region).

Firestore mode: Native (as required) with multi-region location nam5 (North America).
Reason: Firestore “location” is not the same as Cloud Run region; nam5 is the common production choice for US-based apps.

Terraform state: stored in a dedicated GCS backend bucket (created via a tiny bootstrap step).

No importing existing Cloud Run services yet (Phase 2 scope is foundational infra; we’ll codify Cloud Run/IAM for services later when you’re ready to import).

Proposed Terraform folder structure (minimal but production-ready)
infra/
  bootstrap/
    main.tf
    variables.tf
    outputs.tf

  envs/
    dev/
      backend.tf
      main.tf
      variables.tf
      outputs.tf

  modules/
    project_services/
      main.tf
      variables.tf
    iam/
      main.tf
      variables.tf
    storage/
      main.tf
      variables.tf
      outputs.tf
    pubsub/
      main.tf
      variables.tf
      outputs.tf
    firestore/
      main.tf
      variables.tf
      outputs.tf
    service_accounts/
      main.tf
      variables.tf
      outputs.tf


Why this layout

bootstrap/ exists only to create the remote-state bucket (Terraform can’t use a backend bucket that doesn’t exist yet).

envs/dev composes modules.

modules/ keeps each concern isolated and reviewable.

Resources to be created in Phase 2
1) Enable required APIs (via Terraform)

Minimum set for Phase 2 foundation:

run.googleapis.com (Cloud Run)

artifactregistry.googleapis.com (already used)

cloudbuild.googleapis.com (already used)

secretmanager.googleapis.com (secrets exist; TF grants access later)

firestore.googleapis.com

pubsub.googleapis.com

storage.googleapis.com

iam.googleapis.com

serviceusage.googleapis.com

(Optionally now, but harmless and commonly needed soon: logging.googleapis.com, monitoring.googleapis.com.)

2) Service accounts (created now; used in later phases)

Create these SAs now so IAM is codified early:

orchestrator-api-sa — runtime identity for orchestrator Cloud Run service

fetcher-worker-sa — later for fetcher service / worker

evidence-synth-sa — later for Perplexity synthesis service / worker (still web-facing but not debate)

debate-runner-sa — later for debate services (web-blind, internal)

artifact-writer-sa — later for artifact persistence + indexing

3) Firestore (Native mode)

Create the Firestore database for the project (one per project)

Location: nam5

4) Pub/Sub

Topic: ars-jobs

Subscription: ars-jobs-sub (pull)
(We can add DLQ later; out of Phase 2 scope.)

5) GCS buckets (with versioning)

evidence snapshots bucket (immutable snapshots conceptually)

artifacts bucket (ART-xxxxx outputs)

charts bucket (regenerated outputs)

Production defaults:

Uniform bucket-level access = true

Versioning = enabled

Lifecycle rule: keep noncurrent versions for some time (prevents cost runaway)

IAM decisions (clear + minimal)

We’ll keep roles tight and scoped to buckets/topics:

Storage

Grant these roles on specific buckets (not project-wide):

roles/storage.objectAdmin to identities that need to write objects (services)

Optionally roles/storage.objectViewer if a service only reads

Pub/Sub

Publisher: roles/pubsub.publisher on the topic (orchestrator will publish jobs later)

Subscriber: roles/pubsub.subscriber on the subscription (workers consume jobs later)

Firestore

roles/datastore.user for services that read/write chat memory and metadata
(Firestore uses Datastore IAM roles.)

Secret Manager

Phase 2 rule says Terraform grants access but does not create secrets.
We’ll grant secret accessor later once we know exact secret names, or we can grant broad accessor with a prefix policy if your org allows it (often it doesn’t). For now we enable the API; we don’t bind secrets yet unless you want to provide secret resource IDs.

Terraform code (incremental, pasteable)

Below is a complete working skeleton. Start with bootstrap, then envs/dev.

A) infra/bootstrap — create the Terraform remote state bucket
infra/bootstrap/variables.tf
variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "tf_state_bucket_name" {
  type = string
  # Example: "ai-research-studio-tfstate"
}

infra/bootstrap/main.tf
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_storage_bucket" "tf_state" {
  name                        = var.tf_state_bucket_name
  location                    = var.region
  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      num_newer_versions = 10
    }
    action {
      type = "Delete"
    }
  }
}

infra/bootstrap/outputs.tf
output "tf_state_bucket" {
  value = google_storage_bucket.tf_state.name
}


Bootstrap apply (local state is fine here):

cd infra/bootstrap
terraform init
terraform apply -var="project_id=ai-research-studio" -var="tf_state_bucket_name=ai-research-studio-tfstate"

B) infra/envs/dev — main Phase 2 infrastructure
infra/envs/dev/backend.tf
terraform {
  backend "gcs" {
    bucket = "ai-research-studio-tfstate"
    prefix = "envs/dev"
  }
}

infra/envs/dev/variables.tf
variable "project_id" {
  type = string
  default = "ai-research-studio"
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "env" {
  type    = string
  default = "dev"
}

variable "firestore_location_id" {
  type    = string
  default = "nam5"
}

variable "bucket_prefix" {
  type    = string
  default = "ars"
}

infra/envs/dev/main.tf
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

module "project_services" {
  source     = "../../modules/project_services"
  project_id = var.project_id
}

module "service_accounts" {
  source     = "../../modules/service_accounts"
  project_id = var.project_id
  env        = var.env
}

module "firestore" {
  source               = "../../modules/firestore"
  project_id           = var.project_id
  firestore_location_id = var.firestore_location_id

  depends_on = [module.project_services]
}

module "pubsub" {
  source     = "../../modules/pubsub"
  project_id = var.project_id
  env        = var.env

  depends_on = [module.project_services]
}

module "storage" {
  source      = "../../modules/storage"
  project_id  = var.project_id
  region      = var.region
  env         = var.env
  bucket_prefix = var.bucket_prefix

  depends_on = [module.project_services]
}

module "iam" {
  source     = "../../modules/iam"
  project_id = var.project_id

  # Service accounts
  orchestrator_sa = module.service_accounts.orchestrator_sa_email
  fetcher_sa      = module.service_accounts.fetcher_sa_email
  synth_sa        = module.service_accounts.synth_sa_email
  debate_sa       = module.service_accounts.debate_sa_email
  artifact_sa     = module.service_accounts.artifact_sa_email

  # Pub/Sub
  topic_id         = module.pubsub.topic_id
  subscription_id  = module.pubsub.subscription_id

  # Buckets
  bucket_evidence  = module.storage.bucket_evidence
  bucket_artifacts = module.storage.bucket_artifacts
  bucket_charts    = module.storage.bucket_charts
}

infra/envs/dev/outputs.tf
output "service_accounts" {
  value = {
    orchestrator = module.service_accounts.orchestrator_sa_email
    fetcher      = module.service_accounts.fetcher_sa_email
    synth        = module.service_accounts.synth_sa_email
    debate       = module.service_accounts.debate_sa_email
    artifact     = module.service_accounts.artifact_sa_email
  }
}

output "buckets" {
  value = {
    evidence  = module.storage.bucket_evidence
    artifacts = module.storage.bucket_artifacts
    charts    = module.storage.bucket_charts
  }
}

output "pubsub" {
  value = {
    topic        = module.pubsub.topic_id
    subscription = module.pubsub.subscription_id
  }
}

C) Modules
modules/project_services/main.tf
variable "project_id" { type = string }

locals {
  services = [
    "serviceusage.googleapis.com",
    "iam.googleapis.com",
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "secretmanager.googleapis.com",
    "firestore.googleapis.com",
    "pubsub.googleapis.com",
    "storage.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
  ]
}

resource "google_project_service" "enabled" {
  for_each           = toset(local.services)
  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

modules/service_accounts/main.tf
variable "project_id" { type = string }
variable "env" { type = string }

resource "google_service_account" "orchestrator" {
  account_id   = "orchestrator-api-sa-${var.env}"
  display_name = "Orchestrator API Service Account (${var.env})"
}

resource "google_service_account" "fetcher" {
  account_id   = "fetcher-worker-sa-${var.env}"
  display_name = "Fetcher Worker Service Account (${var.env})"
}

resource "google_service_account" "synth" {
  account_id   = "evidence-synth-sa-${var.env}"
  display_name = "Evidence Synthesis Service Account (${var.env})"
}

resource "google_service_account" "debate" {
  account_id   = "debate-runner-sa-${var.env}"
  display_name = "Debate Runner Service Account (${var.env})"
}

resource "google_service_account" "artifact" {
  account_id   = "artifact-writer-sa-${var.env}"
  display_name = "Artifact Writer Service Account (${var.env})"
}

modules/service_accounts/outputs.tf
output "orchestrator_sa_email" { value = google_service_account.orchestrator.email }
output "fetcher_sa_email"      { value = google_service_account.fetcher.email }
output "synth_sa_email"        { value = google_service_account.synth.email }
output "debate_sa_email"       { value = google_service_account.debate.email }
output "artifact_sa_email"     { value = google_service_account.artifact.email }

modules/firestore/main.tf
variable "project_id" { type = string }
variable "firestore_location_id" { type = string }

resource "google_firestore_database" "default" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.firestore_location_id
  type        = "FIRESTORE_NATIVE"
}

modules/firestore/outputs.tf
output "firestore_name" {
  value = google_firestore_database.default.name
}

modules/pubsub/main.tf
variable "project_id" { type = string }
variable "env" { type = string }

resource "google_pubsub_topic" "jobs" {
  name    = "ars-jobs-${var.env}"
  project = var.project_id
}

resource "google_pubsub_subscription" "jobs_sub" {
  name  = "ars-jobs-sub-${var.env}"
  topic = google_pubsub_topic.jobs.name

  ack_deadline_seconds = 30

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
}

modules/pubsub/outputs.tf
output "topic_id" {
  value = google_pubsub_topic.jobs.id
}

output "subscription_id" {
  value = google_pubsub_subscription.jobs_sub.id
}

modules/storage/main.tf
variable "project_id" { type = string }
variable "region" { type = string }
variable "env" { type = string }
variable "bucket_prefix" { type = string }

locals {
  suffix = "${var.project_id}-${var.env}"
}

resource "google_storage_bucket" "evidence" {
  name                        = "${var.bucket_prefix}-evidence-${local.suffix}"
  location                    = var.region
  uniform_bucket_level_access = true

  versioning { enabled = true }

  lifecycle_rule {
    condition { num_newer_versions = 20 }
    action { type = "Delete" }
  }
}

resource "google_storage_bucket" "artifacts" {
  name                        = "${var.bucket_prefix}-artifacts-${local.suffix}"
  location                    = var.region
  uniform_bucket_level_access = true

  versioning { enabled = true }

  lifecycle_rule {
    condition { num_newer_versions = 20 }
    action { type = "Delete" }
  }
}

resource "google_storage_bucket" "charts" {
  name                        = "${var.bucket_prefix}-charts-${local.suffix}"
  location                    = var.region
  uniform_bucket_level_access = true

  versioning { enabled = true }

  lifecycle_rule {
    condition { num_newer_versions = 20 }
    action { type = "Delete" }
  }
}

modules/storage/outputs.tf
output "bucket_evidence"  { value = google_storage_bucket.evidence.name }
output "bucket_artifacts" { value = google_storage_bucket.artifacts.name }
output "bucket_charts"    { value = google_storage_bucket.charts.name }

modules/iam/main.tf
variable "project_id" { type = string }

variable "orchestrator_sa" { type = string }
variable "fetcher_sa"      { type = string }
variable "synth_sa"        { type = string }
variable "debate_sa"       { type = string }
variable "artifact_sa"     { type = string }

variable "topic_id"        { type = string }
variable "subscription_id" { type = string }

variable "bucket_evidence"  { type = string }
variable "bucket_artifacts" { type = string }
variable "bucket_charts"    { type = string }

locals {
  orchestrator = "serviceAccount:${var.orchestrator_sa}"
  fetcher      = "serviceAccount:${var.fetcher_sa}"
  synth        = "serviceAccount:${var.synth_sa}"
  debate       = "serviceAccount:${var.debate_sa}"
  artifact     = "serviceAccount:${var.artifact_sa}"
}

# ---- Firestore access (Datastore role applies to Firestore) ----
resource "google_project_iam_member" "firestore_orchestrator" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = local.orchestrator
}

resource "google_project_iam_member" "firestore_workers" {
  for_each = toset([local.fetcher, local.synth, local.debate, local.artifact])
  project  = var.project_id
  role     = "roles/datastore.user"
  member   = each.value
}

# ---- Pub/Sub ----
resource "google_pubsub_topic_iam_member" "orchestrator_publisher" {
  topic  = var.topic_id
  role   = "roles/pubsub.publisher"
  member = local.orchestrator
}

resource "google_pubsub_subscription_iam_member" "workers_subscriber" {
  for_each     = toset([local.fetcher, local.synth, local.debate, local.artifact])
  subscription = var.subscription_id
  role         = "roles/pubsub.subscriber"
  member       = each.value
}

# ---- Storage: bucket-level permissions ----
# Evidence bucket: fetcher writes snapshots; synth reads; orchestrator reads; artifact may read.
resource "google_storage_bucket_iam_member" "evidence_fetcher_write" {
  bucket = var.bucket_evidence
  role   = "roles/storage.objectAdmin"
  member = local.fetcher
}

resource "google_storage_bucket_iam_member" "evidence_readers" {
  for_each = toset([local.orchestrator, local.synth, local.artifact])
  bucket   = var.bucket_evidence
  role     = "roles/storage.objectViewer"
  member   = each.value
}

# Artifacts bucket: artifact writer writes; orchestrator reads/writes metadata later
resource "google_storage_bucket_iam_member" "artifacts_writer" {
  bucket = var.bucket_artifacts
  role   = "roles/storage.objectAdmin"
  member = local.artifact
}

resource "google_storage_bucket_iam_member" "artifacts_orchestrator_read" {
  bucket = var.bucket_artifacts
  role   = "roles/storage.objectViewer"
  member = local.orchestrator
}

# Charts bucket: artifact or debate runner may write regenerated outputs later
resource "google_storage_bucket_iam_member" "charts_writer" {
  bucket = var.bucket_charts
  role   = "roles/storage.objectAdmin"
  member = local.artifact
}

resource "google_storage_bucket_iam_member" "charts_orchestrator_read" {
  bucket = var.bucket_charts
  role   = "roles/storage.objectViewer"
  member = local.orchestrator
}

Apply steps (Phase 2)
1) Bootstrap backend bucket
cd infra/bootstrap
terraform init
terraform apply -var="project_id=ai-research-studio" -var="tf_state_bucket_name=ai-research-studio-tfstate"

2) Initialize dev environment with remote state
cd infra/envs/dev
terraform init
terraform apply

Phase II architecture: 
                    ┌──────────────────────────┐
                    │        User / Client     │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │     Orchestrator API     │
                    │   Cloud Run (FastAPI)   │
                    │   SA: orchestrator-*    │
                    └────────────┬─────────────┘
                                 │
                ┌────────────────┴────────────────┐
                │                                 │
                ▼                                 ▼
     ┌─────────────────────┐          ┌─────────────────────┐
     │     Firestore        │          │     Pub/Sub Topic   │
     │  (Native, nam5)     │          │   ars-jobs-dev      │
     │                     │          └─────────┬───────────┘
     │  - chat sessions    │                    │
     │  - message lineage  │                    ▼
     │  - artifact index   │          ┌─────────────────────┐
     └─────────────────────┘          │  Pub/Sub Subscription│
                                      │ ars-jobs-sub-dev     │
                                      └─────────┬───────────┘
                                                │
                                                ▼
                        ┌────────────────────────────────────────┐
                        │          Worker Services (Future)       │
                        │----------------------------------------│
                        │  Fetcher      → SA: fetcher-*          │
                        │  Synth        → SA: evidence-synth-*   │
                        │  Debate       → SA: debate-runner-*    │
                        │  Artifact     → SA: artifact-writer-*  │
                        └─────────┬───────────────┬─────────────┘
                                  │               │
                ┌─────────────────▼───┐   ┌──────▼────────────────┐
                │   GCS Evidence       │   │   GCS Artifacts       │
                │ ars-evidence-*       │   │ ars-artifacts-*      │
                │ Immutable snapshots  │   │ ART-xxxxx outputs    │
                └─────────────────────┘   └──────────────────────┘
                                  │
                                  ▼
                         ┌──────────────────────┐
                         │     GCS Charts       │
                         │ ars-charts-*         │
                         │ Regenerated outputs  │
                         └──────────────────────┘

######### PHASE III FAST API ORCHESTRATOR & FIRESTORE JOURNAL DESIGN #############################

┌───────────────────────────────────────────────────────────┐
│                        USER REQUEST                        │
│        POST /chat  (user_id, conversation_id, text)        │
└───────────────────────────────────────────────────────────┘
                             │
                             ▼
┌───────────────────────────────────────────────────────────┐
│                    FASTAPI ORCHESTRATOR                   │
│                 (ONLY component touching Firestore)       │
└───────────────────────────────────────────────────────────┘
         │                         │
         │                         │
         ▼                         ▼
┌──────────────────────┐   ┌──────────────────────────────┐
│  Conversation Doc    │   │        Rehydration            │
│  conversations/c-123 │   │  Load last N messages (seq)   │
│──────────────────────│   │──────────────────────────────│
│ user_id              │   │  messages ordered by seq ASC │
│ next_seq = 7         │   │  role + content only         │
│ last_message_seq=6   │   └──────────────────────────────┘
│ rehydration: last_24 │
└─────────┬────────────┘
          │
          │
          ▼
┌───────────────────────────────────────────────────────────┐
│                       MESSAGES                             │
│     conversations/c-123/messages/{seq}                    │
├──────────────┬──────────────┬──────────────┬─────────────┤
│ seq=1        │ seq=2        │ seq=3        │ seq=4       │
│ role=user    │ role=assist  │ role=user    │ role=assist │
│ "hello"      │ "hi"         │ "explain"    │ "answer"   │
├──────────────┴──────────────┴──────────────┴─────────────┤
│ seq=5        │ seq=6        │                              │
│ role=user    │ role=assist  │                              │
│ "phase 2?"   │ "details"   │                              │
└───────────────────────────────────────────────────────────┘
                             │
                             ▼
┌───────────────────────────────────────────────────────────┐
│             APPEND USER MESSAGE (TRANSACTION)              │
│   seq = next_seq (7)                                       │
│   role = user                                              │
│   content = "Explain Phase 3 again"                        │
│   request_id = req-abc:user                                │
│   next_seq → 8                                             │
└───────────────────────────────────────────────────────────┘
                             │
                             ▼
┌───────────────────────────────────────────────────────────┐
│               🔒 LOCKED PIPELINE (UNCHANGED)               │
│                                                           │
│   User Input                                               │
│     → SerpAPI                                              │
│     → Fetcher                                             │
│     → Perplexity (search only)                             │
│     → Evidence Pack (GCS)                                  │
│     → Debate LLMs (web-blind)                              │
│     → Referee                                             │
│     → Structured Output                                   │
│     → ART-000456 (GCS)                                     │
│                                                           │
└───────────────────────────────────────────────────────────┘
                             │
                             ▼
┌───────────────────────────────────────────────────────────┐
│           APPEND ASSISTANT MESSAGE (TRANSACTION)            │
│   seq = 8                                                  │
│   role = assistant                                        │
│   content = "Phase 3 introduces Firestore memory..."       │
│   request_id = req-abc:assistant                           │
│   pipeline.evidence_pack = EVP-000777                      │
│   artifacts = [ART-000456]                                 │
│   next_seq → 9                                             │
└───────────────────────────────────────────────────────────┘
                             │
                             ▼
┌───────────────────────────────────────────────────────────┐
│                     FIRESTORE STATE                        │
│                                                           │
│ Conversation c-123                                        │
│   next_seq = 9                                            │
│                                                           │
│ Messages:                                                  │
│   seq 7 → user                                            │
│   seq 8 → assistant (→ ART-000456)                         │
│                                                           │
└───────────────────────────────────────────────────────────┘
