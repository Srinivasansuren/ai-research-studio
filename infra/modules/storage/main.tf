variable "project_id" { type = string }
variable "region" { type = string }
variable "env" { type = string }
variable "bucket_prefix" { type = string }

locals {
  suffix = "${var.project_id}-${var.env}"
}

resource "google_storage_bucket" "evidence" {
  name                        = "${var.bucket_prefix}-evidence-${local.suffix}"
  location                    = var.region
  uniform_bucket_level_access = true

  versioning { enabled = true }

  lifecycle_rule {
    condition { num_newer_versions = 20 }
    action { type = "Delete" }
  }
}

resource "google_storage_bucket" "artifacts" {
  name                        = "${var.bucket_prefix}-artifacts-${local.suffix}"
  location                    = var.region
  uniform_bucket_level_access = true

  versioning { enabled = true }

  lifecycle_rule {
    condition { num_newer_versions = 20 }
    action { type = "Delete" }
  }
}

resource "google_storage_bucket" "charts" {
  name                        = "${var.bucket_prefix}-charts-${local.suffix}"
  location                    = var.region
  uniform_bucket_level_access = true

  versioning { enabled = true }

  lifecycle_rule {
    condition { num_newer_versions = 20 }
    action { type = "Delete" }
  }
}
