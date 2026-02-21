# Cloud Run Module

Reusable Terraform module for deploying services to Google Cloud Run.

## Usage

```hcl
module "scan_service" {
  source = "./modules/cloud_run"

  name                  = "scan-service"
  project_id            = var.project_id
  region                = var.region
  image                 = "gcr.io/${var.project_id}/scan-service:latest"
  service_account_email = google_service_account.scan_service.email

  # Performance configuration
  min_instances = 2
  max_instances = 100
  concurrency   = 80
  timeout       = "60s"

  # Resources
  cpu        = "1"
  memory     = "512Mi"
  cpu_idle   = true

  # Health check
  health_check_path = "/v1/health"
  port              = 8080

  # Environment variables
  env_vars = {
    ENV               = "production"
    REDIS_ADDR        = "10.0.0.3:6379"
    GCP_PROJECT_ID    = var.project_id
  }

  # Secrets
  secrets = {
    DATABASE_URL = {
      secret  = "database-url"
      version = "latest"
    }
    REDIS_PASSWORD = {
      secret  = "redis-auth"
      version = "latest"
    }
  }

  # Network
  ingress = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER_ONLY"
}
```

## Variables

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| name | Service name | string | - | yes |
| project_id | GCP project ID | string | - | yes |
| region | GCP region | string | - | yes |
| image | Container image | string | - | yes |
| service_account_email | Service account | string | - | yes |
| port | Container port | number | 8080 | no |
| min_instances | Min instances | number | 0 | no |
| max_instances | Max instances | number | 10 | no |
| concurrency | Max concurrent requests | number | 80 | no |
| timeout | Request timeout | string | "60s" | no |
| cpu | CPU allocation | string | "1" | no |
| memory | Memory allocation | string | "512Mi" | no |
| cpu_idle | CPU idle (scale to zero) | bool | true | no |
| health_check_path | Health check path | string | "/v1/health" | no |
| env_vars | Environment variables | map(string) | {} | no |
| secrets | Secret env variables | map(object) | {} | no |
| ingress | Ingress traffic setting | string | INTERNAL_ONLY | no |

## Outputs

| Name | Description |
|------|-------------|
| service_name | Cloud Run service name |
| service_url | Cloud Run service URL |
| service_id | Cloud Run service ID |
