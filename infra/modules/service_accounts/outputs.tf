output "orchestrator_sa_email" { value = google_service_account.orchestrator.email }
output "fetcher_sa_email"      { value = google_service_account.fetcher.email }
output "synth_sa_email"        { value = google_service_account.synth.email }
output "debate_sa_email"       { value = google_service_account.debate.email }
output "artifact_sa_email"     { value = google_service_account.artifact.email }
output "pipeline_runner_sa_email" { value = google_service_account.pipeline_runner.email }
