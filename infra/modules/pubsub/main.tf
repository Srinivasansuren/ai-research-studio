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
