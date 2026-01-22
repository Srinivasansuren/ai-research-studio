resource "google_service_account" "sa" {
  account_id   = "${var.service_name}-sa"
  display_name = "${var.service_name} service account"
  project      = var.project_id
}

# Allow this worker to read/write GCS evidence bucket
resource "google_storage_bucket_iam_member" "bucket_rw" {
  bucket = var.evidence_bucket
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.sa.email}"
}

# Allow Firestore access (jobs state updates)
resource "google_project_iam_member" "firestore_user" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.sa.email}"
}

# Pub/Sub topic for synth requests
resource "google_pubsub_topic" "topic" {
  name    = var.pubsub_topic_name
  project = var.project_id
}

# Push subscription to Cloud Run
resource "google_pubsub_subscription" "push" {
  name    = "${var.pubsub_topic_name}-push"
  project = var.project_id
  topic   = google_pubsub_topic.topic.name

  ack_deadline_seconds = 60

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  push_config {
    push_endpoint = "${google_cloud_run_v2_service.svc.uri}/pubsub/push"

    oidc_token {
      service_account_email = google_service_account.sa.email
    }
  }
}

# Cloud Run service
resource "google_cloud_run_v2_service" "svc" {
  name     = var.service_name
  location = var.region
  project  = var.project_id

  template {
    service_account = google_service_account.sa.email

    containers {
      image = var.image

      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }

      env {
        name  = "FIRESTORE_DATABASE"
        value = var.firestore_database
      }

      env {
        name  = "EVIDENCE_BUCKET"
        value = var.evidence_bucket
      }

      # Secret Manager lookup parameters (worker fetches secrets at runtime)
      env {
        name  = "PERPLEXITY_SECRET_PROJECT_ID"
        value = var.perplexity_secret_project_id
      }

      env {
        name  = "PERPLEXITY_SECRET_NAME"
        value = var.perplexity_secret_name
      }

      env {
        name  = "PERPLEXITY_SECRET_VERSION"
        value = var.perplexity_secret_version
      }

      env {
        name  = "PIPELINE_VERSION"
        value = var.pipeline_version
      }

      env {
        name  = "PROMPT_VERSION"
        value = var.prompt_version
      }

      env {
        name  = "MAX_EVIDENCE_CHARS_TOTAL"
        value = tostring(var.max_evidence_chars_total)
      }
    }
  }

  depends_on = [
    google_project_iam_member.firestore_user,
    google_storage_bucket_iam_member.bucket_rw,
  ]
}
