# -------------------------------------------------------------------
# Core identifiers (REQUIRED by module implementation)
# -------------------------------------------------------------------

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
}

variable "service_name" {
  description = "Cloud Run service name"
  type        = string
}

# -------------------------------------------------------------------
# Container image
# -------------------------------------------------------------------

variable "image" {
  description = "Container image URI for the perplexity synth worker"
  type        = string
}

# -------------------------------------------------------------------
# Firestore
# -------------------------------------------------------------------

variable "firestore_database" {
  description = "Firestore database ID (usually '(default)')"
  type        = string
}

# -------------------------------------------------------------------
# Storage
# -------------------------------------------------------------------

variable "evidence_bucket" {
  description = "Evidence GCS bucket"
  type        = string
}

# -------------------------------------------------------------------
# Pub/Sub
# -------------------------------------------------------------------

variable "pubsub_topic_name" {
  description = "Pub/Sub topic name for perplexity synth requests"
  type        = string
}

# -------------------------------------------------------------------
# Perplexity secret lookup (Secret Manager)
# -------------------------------------------------------------------

variable "perplexity_secret_project_id" {
  description = "Project ID where the Perplexity API key secret lives"
  type        = string
}

variable "perplexity_secret_name" {
  description = "Secret Manager secret name for Perplexity API key"
  type        = string
}

variable "perplexity_secret_version" {
  description = "Secret Manager secret version"
  type        = string
  default     = "latest"
}

# -------------------------------------------------------------------
# Pipeline / prompt controls
# -------------------------------------------------------------------

variable "pipeline_version" {
  description = "Pipeline version string"
  type        = string
}

variable "prompt_version" {
  description = "Prompt version string"
  type        = string
}

variable "max_evidence_chars_total" {
  description = "Maximum total evidence size (characters)"
  type        = number
}
