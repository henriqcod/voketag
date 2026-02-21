terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

variable "name" {
  description = "Service name"
  type        = string
}

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
}

variable "image" {
  description = "Container image"
  type        = string
}

variable "service_account_email" {
  description = "Service account email"
  type        = string
}

variable "port" {
  description = "Container port"
  type        = number
  default     = 8080
}

variable "min_instances" {
  description = "Minimum number of instances"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum number of instances"
  type        = number
  default     = 10
}

variable "concurrency" {
  description = "Max concurrent requests per instance"
  type        = number
  default     = 80
}

variable "timeout" {
  description = "Request timeout"
  type        = string
  default     = "60s"
}

variable "cpu" {
  description = "CPU allocation"
  type        = string
  default     = "1"
}

variable "memory" {
  description = "Memory allocation"
  type        = string
  default     = "512Mi"
}

variable "cpu_idle" {
  description = "Enable CPU idle (scale to zero)"
  type        = bool
  default     = true
}

variable "health_check_path" {
  description = "Health check endpoint path"
  type        = string
  default     = "/v1/health"
}

variable "env_vars" {
  description = "Environment variables"
  type        = map(string)
  default     = {}
}

variable "secrets" {
  description = "Secret environment variables"
  type = map(object({
    secret  = string
    version = string
  }))
  default = {}
}

variable "ingress" {
  description = "Ingress traffic setting"
  type        = string
  default     = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER_ONLY"
}

# Cloud Run Service
resource "google_cloud_run_v2_service" "service" {
  name     = var.name
  location = var.region
  project  = var.project_id

  template {
    service_account    = var.service_account_email
    max_instance_count = var.max_instances
    min_instance_count = var.min_instances
    timeout            = var.timeout

    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    containers {
      image = var.image

      max_instance_request_concurrency = var.concurrency

      ports {
        container_port = var.port
      }

      resources {
        limits = {
          cpu    = var.cpu
          memory = var.memory
        }
        cpu_idle = var.cpu_idle
      }

      # Environment variables
      dynamic "env" {
        for_each = var.env_vars
        content {
          name  = env.key
          value = env.value
        }
      }

      # Secret environment variables
      dynamic "env" {
        for_each = var.secrets
        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = env.value.secret
              version = env.value.version
            }
          }
        }
      }

      # Startup probe
      startup_probe {
        http_get {
          path = var.health_check_path
          port = var.port
        }
        initial_delay_seconds = 0
        timeout_seconds       = 3
        period_seconds        = 10
        failure_threshold     = 3
      }

      # Liveness probe
      liveness_probe {
        http_get {
          path = var.health_check_path
          port = var.port
        }
        initial_delay_seconds = 0
        timeout_seconds       = 3
        period_seconds        = 30
        failure_threshold     = 3
      }
    }

    execution_environment = "EXECUTION_ENVIRONMENT_GEN2"
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  ingress = var.ingress
}

# Outputs
output "service_name" {
  description = "Cloud Run service name"
  value       = google_cloud_run_v2_service.service.name
}

output "service_url" {
  description = "Cloud Run service URL"
  value       = google_cloud_run_v2_service.service.uri
}

output "service_id" {
  description = "Cloud Run service ID"
  value       = google_cloud_run_v2_service.service.id
}
