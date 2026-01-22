data "google_cloud_run_service" "fetcher" {
  name     = var.fetcher_cloud_run_service_name
  location = var.region
  project  = var.project_id
}

locals {
  fetcher_url = data.google_cloud_run_service.fetcher.status[0].url
}


locals {
  fetch_topic_name        = "${var.fetch_topic_name_prefix}-${var.env}"
  fetch_subscription_name = "${var.fetch_push_subscription_name_prefix}-${var.env}"

  # We only create push wiring if URL is provided
  enable_push = length(trimspace(local.fetcher_url)) > 0
}

# 1) Dedicated topic for fetch requests (DO NOT reuse ars-jobs-*)
resource "google_pubsub_topic" "fetch_requests" {
  name    = local.fetch_topic_name
  project = var.project_id
}

# 2) Orchestrator publishes fetch jobs
resource "google_pubsub_topic_iam_member" "orchestrator_publisher" {
  project = var.project_id
  topic   = google_pubsub_topic.fetch_requests.name
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${var.orchestrator_service_account_email}"
}

# 3) Service account used by Pub/Sub push to authenticate to Cloud Run
resource "google_service_account" "pubsub_push_invoker" {
  account_id   = "${var.pubsub_push_invoker_sa_name}-${var.env}"
  display_name = "PubSub push invoker (${var.env})"
  project      = var.project_id
}

# 4) Allow that SA to invoke the fetcher-worker Cloud Run service (created only when URL is known)
resource "google_cloud_run_service_iam_member" "fetcher_invoker" {
  count    = local.enable_push ? 1 : 0
  project  = var.project_id
  location = var.region
  service  = var.fetcher_cloud_run_service_name

  role   = "roles/run.invoker"
  member = "serviceAccount:${google_service_account.pubsub_push_invoker.email}"
}

# 5) Push subscription to fetcher-worker (created only when URL is known)
resource "google_pubsub_subscription" "fetch_requests_push" {
  count   = local.enable_push ? 1 : 0
  name    = local.fetch_subscription_name
  topic   = google_pubsub_topic.fetch_requests.id
  project = var.project_id

  ack_deadline_seconds = 60

  push_config {
    push_endpoint = "${local.fetcher_url}/pubsub/push"

    oidc_token {
      service_account_email = google_service_account.pubsub_push_invoker.email
      audience              = local.fetcher_url
    }
  }

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
}
