output "service_name" {
  value = google_cloud_run_v2_service.svc.name
}

output "service_url" {
  value = google_cloud_run_v2_service.svc.uri
}

output "sa_email" {
  value = google_service_account.sa.email
}

output "topic" {
  value = google_pubsub_topic.topic.name
}

output "subscription" {
  value = google_pubsub_subscription.push.name
}
