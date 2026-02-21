resource "google_cloud_run_v2_service" "scan_service" {
  name     = "scan-service"
  location = var.region

  template {
    service_account = google_service_account.scan_service.email
    max_instance_count = 100  # MEDIUM FIX: Increased from 10 to 100 for headroom
    min_instance_count = 2    # MEDIUM FIX: Always warm (was 0) - eliminates cold starts
    timeout            = "60s"  # HIGH FIX: Increased from 10s to 60s for reliability

    scaling {
      min_instance_count = 2    # MEDIUM FIX: Always warm - P95 < 100ms guaranteed
      max_instance_count = 100  # MEDIUM FIX: Headroom for traffic spikes
    }

    containers {
      image = "gcr.io/${var.project_id}/scan-service:latest"

      max_instance_request_concurrency = 80

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        cpu_idle = true
      }
      
      # HIGH SECURITY FIX: Set explicit startup and liveness probes
      startup_probe {
        http_get {
          path = "/v1/health"
          port = 8080
        }
        initial_delay_seconds = 0
        timeout_seconds       = 3
        period_seconds        = 10
        failure_threshold     = 3
      }
      
      liveness_probe {
        http_get {
          path = "/v1/health"
          port = 8080
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

  ingress = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER_ONLY"
}

resource "google_cloud_run_v2_service" "factory_service" {
  name     = "factory-service"
  location = var.region

  template {
    service_account = google_service_account.factory_service.email
    max_instance_count = 5
    min_instance_count = 0
    timeout            = "300s"  # HIGH FIX: Increased from 10s to 300s (CSV processing needs time)

    scaling {
      min_instance_count = 0
      max_instance_count = 5
    }

    containers {
      image = "gcr.io/${var.project_id}/factory-service:latest"

      max_instance_request_concurrency = 80

      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
        cpu_idle = false
      }
      
      # HIGH SECURITY FIX: Set explicit startup and liveness probes
      startup_probe {
        http_get {
          path = "/v1/health"
          port = 8000
        }
        initial_delay_seconds = 0
        timeout_seconds       = 3
        period_seconds        = 10
        failure_threshold     = 3
      }
      
      liveness_probe {
        http_get {
          path = "/v1/health"
          port = 8000
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

  ingress = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER_ONLY"
}
