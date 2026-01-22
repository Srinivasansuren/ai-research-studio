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

resource "google_service_account" "pipeline_runner" {
  account_id   = "pipeline-runner-sa-${var.env}"
  display_name = "Pipeline Runner SA (${var.env})"
}
