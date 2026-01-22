output "topic_id" {
  value = google_pubsub_topic.jobs.id
}

output "subscription_id" {
  value = google_pubsub_subscription.jobs_sub.id
}
