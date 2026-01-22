terraform {
  backend "gcs" {
    bucket = "ai-research-studio-tfstate"
    prefix = "envs/dev"
  }
}
