resource "google_sql_user" "factory_iam" {
  name     = google_service_account.factory_service.email
  instance = google_sql_database_instance.main.name
  type     = "CLOUD_IAM_SERVICE_ACCOUNT"
}
