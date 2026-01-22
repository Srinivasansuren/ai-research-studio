output "service_accounts" {
  value = {
    orchestrator = module.service_accounts.orchestrator_sa_email
    fetcher      = module.service_accounts.fetcher_sa_email
    synth        = module.service_accounts.synth_sa_email
    debate       = module.service_accounts.debate_sa_email
    artifact     = module.service_accounts.artifact_sa_email
  }
}

output "buckets" {
  value = {
    evidence  = module.storage.bucket_evidence
    artifacts = module.storage.bucket_artifacts
    charts    = module.storage.bucket_charts
  }
}

output "pubsub" {
  value = {
    topic        = module.pubsub.topic_id
    subscription = module.pubsub.subscription_id
  }
}

output "fetch_requests_topic" {
  value = module.fetcher_pubsub.fetch_requests_topic_name
}

output "fetch_requests_push_subscription" {
  value = module.fetcher_pubsub.fetch_push_subscription_name
}

output "pubsub_push_invoker_sa" {
  value = module.fetcher_pubsub.pubsub_push_invoker_service_account_email
}
