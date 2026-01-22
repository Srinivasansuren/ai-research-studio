terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

module "project_services" {
  source     = "../../modules/project_services"
  project_id = var.project_id
}

module "service_accounts" {
  source     = "../../modules/service_accounts"
  project_id = var.project_id
  env        = var.env
}

module "firestore" {
  source                = "../../modules/firestore"
  project_id            = var.project_id
  firestore_location_id = var.firestore_location_id

  depends_on = [module.project_services]
}

module "pubsub" {
  source     = "../../modules/pubsub"
  project_id = var.project_id
  env        = var.env

  depends_on = [module.project_services]
}

module "storage" {
  source        = "../../modules/storage"
  project_id    = var.project_id
  region        = var.region
  env           = var.env
  bucket_prefix = var.bucket_prefix

  depends_on = [module.project_services]
}

module "iam" {
  source     = "../../modules/iam"
  project_id = var.project_id

  # Service accounts
  orchestrator_sa = module.service_accounts.orchestrator_sa_email
  fetcher_sa      = module.service_accounts.fetcher_sa_email
  synth_sa        = module.service_accounts.synth_sa_email
  debate_sa       = module.service_accounts.debate_sa_email
  artifact_sa     = module.service_accounts.artifact_sa_email

  # Pub/Sub
  topic_id        = module.pubsub.topic_id
  subscription_id = module.pubsub.subscription_id

  # Buckets
  bucket_evidence  = module.storage.bucket_evidence
  bucket_artifacts = module.storage.bucket_artifacts
  bucket_charts    = module.storage.bucket_charts
}

module "fetcher_pubsub" {
  source     = "../../modules/fetcher_pubsub"
  project_id = var.project_id
  region     = var.region
  env        = var.env

  orchestrator_service_account_email = module.service_accounts.orchestrator_sa_email
  fetcher_cloud_run_service_name     = "fetcher-worker"
}

################### PHASE V ADDITION #######################
#############################################################

module "pipeline_runner" {
  source = "../../modules/pipeline_runner"

  project_id     = var.project_id
  project_number = var.project_number
  region         = var.region
  env            = var.env

  pipeline_runner_image = var.pipeline_runner_image
  serpapi_secret_name   = var.serpapi_secret_name

  jobs_topic_id                = module.pubsub.topic_id
  fetch_requests_topic_name    = module.fetcher_pubsub.fetch_requests_topic_name
  evidence_bucket_name         = module.storage.bucket_evidence
  pubsub_push_invoker_sa_email = module.fetcher_pubsub.pubsub_push_invoker_service_account_email
  pipeline_runner_sa_email     = module.service_accounts.pipeline_runner_sa_email
    # >>> REQUIRED FOR PHASE VI <<<
  perplexity_synth_requests_topic = module.perplexity_synth_worker.topic

}


# project_number = var.project_number

############################# PHASE VI #########################
###############################################################

module "perplexity_synth_worker" {
  source = "../../modules/perplexity_synth_worker"

  # REQUIRED CORE
  project_id   = var.project_id
  region       = var.region
  service_name = "perplexity-synth-worker"

  # IMAGE
  image = var.perplexity_synth_worker_image

  # STORAGE / DB
  firestore_database = var.firestore_database
  evidence_bucket    = var.evidence_bucket

  # PUBSUB
  pubsub_topic_name = var.perplexity_synth_requests_topic

  # SECRETS
  perplexity_secret_project_id = var.perplexity_secret_project_id
  perplexity_secret_name       = var.perplexity_secret_name
  perplexity_secret_version    = var.perplexity_secret_version

  # PIPELINE
  pipeline_version         = var.pipeline_version
  prompt_version           = var.prompt_version
  max_evidence_chars_total = var.max_evidence_chars_total
}
