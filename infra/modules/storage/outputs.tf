output "bucket_evidence"  { value = google_storage_bucket.evidence.name }
output "bucket_artifacts" { value = google_storage_bucket.artifacts.name }
output "bucket_charts"    { value = google_storage_bucket.charts.name }
