resource "google_service_account" "scan_service" {
  account_id   = "scan-service-sa"
  display_name = "Scan Service"
  project      = var.project_id
}

resource "google_service_account" "factory_service" {
  account_id   = "factory-service-sa"
  display_name = "Factory Service"
  project      = var.project_id
}

resource "google_service_account" "blockchain_service" {
  account_id   = "blockchain-service-sa"
  display_name = "Blockchain Service"
  project      = var.project_id
}

resource "google_service_account" "admin_service" {
  account_id   = "admin-service-sa"
  display_name = "Admin Service"
  project      = var.project_id
}

resource "google_project_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = "github-pool"
  display_name              = "GitHub Actions"
  description               = "Workload Identity Pool for GitHub Actions"
  project                   = var.project_id
}

resource "google_project_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id          = google_project_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                      = "GitHub Provider"
  project                           = var.project_id

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
  }

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

output "workload_identity_provider" {
  value       = "${var.project_id}.svc.id.goog/${google_project_iam_workload_identity_pool.github.name}/${google_project_iam_workload_identity_pool_provider.github.workload_identity_pool_provider_id}"
  description = "Workload Identity Provider for GitHub Actions"
}
