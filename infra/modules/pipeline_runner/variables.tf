################# PHASE V ADDITION #################################
##########################################################

################# PHASE V #################################

variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "env" {
  type = string
}

variable "pipeline_runner_image" {
  type = string
}

variable "serpapi_secret_name" {
  type = string
}

# Inputs from existing graph
variable "jobs_topic_id" {
  type = string
}

variable "fetch_requests_topic_name" {
  type = string
}

variable "evidence_bucket_name" {
  type = string
}

variable "pubsub_push_invoker_sa_email" {
  type = string
}

variable "pipeline_runner_sa_email" {
  type = string
}

variable "project_number" {
  type = string
}

variable "perplexity_synth_requests_topic" {
  description = "Pub/Sub topic for Perplexity synthesis requests (Phase VI)"
  type        = string
}

