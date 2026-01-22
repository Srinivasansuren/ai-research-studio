variable "project_id" {
  type    = string
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


############################ PHASE V ADDITION ######################
#################################################################

variable "pipeline_runner_image" {
  type = string
}

variable "serpapi_secret_name" {
  type = string
}

variable "project_number" {
  type = string
}

variable "perplexity_synth_worker_image" {
  type = string
}

variable "perplexity_synth_requests_topic" {
  type = string
}

variable "firestore_database" {
  type = string
}

variable "evidence_bucket" {
  type = string
}

variable "perplexity_secret_project_id" {
  type = string
}

variable "perplexity_secret_name" {
  type = string
}

variable "perplexity_secret_version" {
  type    = string
  default = "latest"
}

variable "pipeline_version" {
  type = string
}

variable "prompt_version" {
  type = string
}

variable "max_evidence_chars_total" {
  type = number
}
