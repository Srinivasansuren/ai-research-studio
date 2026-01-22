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
