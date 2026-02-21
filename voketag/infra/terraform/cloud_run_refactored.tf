# LOW ENHANCEMENT: Refactored to use reusable modules
# 
# This file now uses the cloud_run module instead of duplicating configuration.
# See modules/cloud_run/ for the reusable module definition.
#
# Benefits:
# - DRY principle (Don't Repeat Yourself)
# - Easier to maintain (change once, apply everywhere)
# - Consistent configuration across services
# - Less code duplication

# Scan Service - Latency-critical runtime service
module "scan_service" {
  source = "./modules/cloud_run"

  name                  = "scan-service"
  project_id            = var.project_id
  region                = var.region
  image                 = "gcr.io/${var.project_id}/scan-service:latest"
  service_account_email = google_service_account.scan_service.email

  # Performance: Always warm for low latency (P95 < 100ms)
  min_instances = 2
  max_instances = 100
  concurrency   = 80
  timeout       = "60s"

  # Resources
  cpu      = "1"
  memory   = "512Mi"
  cpu_idle = true

  # Health check
  health_check_path = "/v1/health"
  port              = 8080

  # Network: Internal only (behind Load Balancer)
  ingress = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER_ONLY"
}

# Factory Service - Standard CRUD API
module "factory_service" {
  source = "./modules/cloud_run"

  name                  = "factory-service"
  project_id            = var.project_id
  region                = var.region
  image                 = "gcr.io/${var.project_id}/factory-service:latest"
  service_account_email = google_service_account.factory_service.email

  # Performance: Can scale to zero (not latency-critical)
  min_instances = 0
  max_instances = 20
  concurrency   = 80
  timeout       = "300s"  # CSV uploads need time

  # Resources: More memory for CSV processing
  cpu      = "1"
  memory   = "1Gi"
  cpu_idle = false

  # Health check
  health_check_path = "/v1/health"
  port              = 8000

  # Network: Internal only
  ingress = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER_ONLY"
}

# Blockchain Service - Batch processing
module "blockchain_service" {
  source = "./modules/cloud_run"

  name                  = "blockchain-service"
  project_id            = var.project_id
  region                = var.region
  image                 = "gcr.io/${var.project_id}/blockchain-service:latest"
  service_account_email = google_service_account.blockchain_service.email

  # Performance: Always one instance (worker)
  min_instances = 1
  max_instances = 5
  concurrency   = 10  # Lower for heavy processing
  timeout       = "600s"  # Blockchain calls slow

  # Resources: More memory for Merkle trees
  cpu      = "1"
  memory   = "1Gi"
  cpu_idle = false

  # Health check
  health_check_path = "/v1/health"
  port              = 8000

  # Network: Internal only
  ingress = "INGRESS_TRAFFIC_INTERNAL_ONLY"
}

# Admin Service - Simple management UI
module "admin_service" {
  source = "./modules/cloud_run"

  name                  = "admin-service"
  project_id            = var.project_id
  region                = var.region
  image                 = "gcr.io/${var.project_id}/admin-service:latest"
  service_account_email = google_service_account.admin_service.email

  # Performance: Can scale to zero
  min_instances = 0
  max_instances = 3
  concurrency   = 80
  timeout       = "30s"

  # Resources: Minimal (simple Node.js service)
  cpu      = "1"
  memory   = "256Mi"
  cpu_idle = true

  # Health check
  health_check_path = "/v1/health"
  port              = 8080

  # Network: Internal only
  ingress = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER_ONLY"
}

# Outputs
output "scan_service_url" {
  description = "Scan service URL"
  value       = module.scan_service.service_url
}

output "factory_service_url" {
  description = "Factory service URL"
  value       = module.factory_service.service_url
}

output "blockchain_service_url" {
  description = "Blockchain service URL"
  value       = module.blockchain_service.service_url
}

output "admin_service_url" {
  description = "Admin service URL"
  value       = module.admin_service.service_url
}
