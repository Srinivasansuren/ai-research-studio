output "fetch_requests_topic_id" {
  value = google_pubsub_topic.fetch_requests.id
}

output "fetch_requests_topic_name" {
  value = google_pubsub_topic.fetch_requests.name
}

output "pubsub_push_invoker_service_account_email" {
  value = google_service_account.pubsub_push_invoker.email
}

output "fetch_push_subscription_id" {
  value = length(google_pubsub_subscription.fetch_requests_push) > 0 ? google_pubsub_subscription.fetch_requests_push[0].id : ""
}

output "fetch_push_subscription_name" {
  value = length(google_pubsub_subscription.fetch_requests_push) > 0 ? google_pubsub_subscription.fetch_requests_push[0].name : ""
}
