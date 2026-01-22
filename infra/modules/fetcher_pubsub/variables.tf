variable "project_id" { type = string }
variable "region"     { type = string }
variable "env"        { type = string }



# Service account email used by orchestrator-api (already exists in your project)
variable "orchestrator_service_account_email" { type = string }

# Name prefix for the Pub/Sub push invoker service account (module will suffix env)
variable "pubsub_push_invoker_sa_name" {
  type    = string
  default = "pubsub-push-invoker"
}

# Resource names (you can keep defaults)
variable "fetch_topic_name_prefix" {
  type    = string
  default = "ars-fetch-requests"
}

variable "fetch_push_subscription_name_prefix" {
  type    = string
  default = "ars-fetch-requests-push"
}

# Cloud Run service name for fetcher (matches gcloud run deploy fetcher-worker)
variable "fetcher_cloud_run_service_name" {
  type    = string
  default = "fetcher-worker"
}
