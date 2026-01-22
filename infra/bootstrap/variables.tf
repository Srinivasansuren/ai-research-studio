variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "tf_state_bucket_name" {
  type = string
  # Example: "ai-research-studio-tfstate"
}
