data "google_project" "this" {
  project_id = var.project_id
}

# 1) Cloud Run service: pipeline-runner
resource "google_cloud_run_v2_service" "pipeline_runner" {
  name     = "pipeline-runner"
  location = var.region
  deletion_protection = true

  template {
    service_account = var.pipeline_runner_sa_email

    containers {
      image = var.pipeline_runner_image

      env {
        name  = "ENV"
        value = var.env
      }

      # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
      # REQUIRED (Pydantic Settings.project_id)
      # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }

      # Pipeline Runner needs to publish fetch requests
      env {
        name  = "FETCH_REQUESTS_TOPIC"
        value = var.fetch_requests_topic_name
      }

      # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
      # REQUIRED (Pydantic Settings.perplexity_synth_topic)
      # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
      env {
        name  = "PERPLEXITY_SYNTH_TOPIC"
        value = var.perplexity_synth_requests_topic
      }

      # Evidence bucket name for reads
      env {
        name  = "EVIDENCE_BUCKET"
        value = var.evidence_bucket_name
      }

      # SerpAPI key comes from Secret Manager
      env {
        name = "SERPAPI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = var.serpapi_secret_name
            version = "latest"
          }
        }
      }
    }
  }

  ingress = "INGRESS_TRAFFIC_ALL" # keep consistent with your current push pattern
}

# Allow Pub/Sub push invoker SA to call pipeline-runner
resource "google_cloud_run_v2_service_iam_member" "pipeline_runner_invoker" {
  location = var.region
  name     = google_cloud_run_v2_service.pipeline_runner.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${var.pubsub_push_invoker_sa_email}"
}

# 2) Pub/Sub push subscription (jobs -> pipeline runner)
resource "google_pubsub_subscription" "jobs_push_to_pipeline_runner" {
  name  = "ars-jobs-push-to-pipeline-runner-${var.env}"
  topic = var.jobs_topic_id

  ack_deadline_seconds = 60

  push_config {
    push_endpoint = "${google_cloud_run_v2_service.pipeline_runner.uri}/pubsub/push"
    oidc_token {
      service_account_email = var.pubsub_push_invoker_sa_email
    }
  }

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
}

# 3) Evidence-written eventing: GCS finalize -> Pub/Sub topic -> push to pipeline runner

resource "google_pubsub_topic" "evidence_written" {
  name = "ars-evidence-written-${var.env}"
}

# Grant GCS notifications SA permission to publish to the topic
# GCS uses: service-${PROJECT_NUMBER}@gs-project-accounts.iam.gserviceaccount.com
resource "google_pubsub_topic_iam_member" "gcs_publisher" {
  topic  = google_pubsub_topic.evidence_written.name
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:service-${data.google_project.this.number}@gs-project-accounts.iam.gserviceaccount.com"
}

# GCS notification on evidence bucket object finalize
resource "google_storage_notification" "evidence_bucket_finalize_to_pubsub" {
  bucket         = var.evidence_bucket_name
  topic          = google_pubsub_topic.evidence_written.id
  payload_format = "JSON_API_V1"
  event_types    = ["OBJECT_FINALIZE"]
}

# Push evidence-written topic to pipeline runner too
resource "google_pubsub_subscription" "evidence_written_push_to_pipeline_runner" {
  name  = "ars-evidence-written-push-to-pipeline-runner-${var.env}"
  topic = google_pubsub_topic.evidence_written.id

  ack_deadline_seconds = 60

  push_config {
    push_endpoint = "${google_cloud_run_v2_service.pipeline_runner.uri}/pubsub/push"
    oidc_token {
      service_account_email = var.pubsub_push_invoker_sa_email
    }
  }

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
}

############################ PHASE V ADDITION ######################
##################################################################

# Pipeline runner → publish fetch requests
resource "google_pubsub_topic_iam_member" "publisher_fetch_requests" {
  topic  = var.fetch_requests_topic_name
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:${var.pipeline_runner_sa_email}"
}

# Pipeline runner → write evidence snapshots
resource "google_storage_bucket_iam_member" "evidence_object_admin" {
  bucket = var.evidence_bucket_name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.pipeline_runner_sa_email}"
}

# Pipeline runner → Firestore job state
resource "google_project_iam_member" "firestore_user" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${var.pipeline_runner_sa_email}"
}

# Pipeline runner → SerpAPI secret access
resource "google_secret_manager_secret_iam_member" "serpapi_accessor" {
  secret_id = var.serpapi_secret_name
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.pipeline_runner_sa_email}"
}

resource "google_pubsub_topic_iam_member" "gcs_service_agent_publisher" {
  topic  = google_pubsub_topic.evidence_written.name
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:service-${var.project_number}@gs-project-accounts.iam.gserviceaccount.com"
}
