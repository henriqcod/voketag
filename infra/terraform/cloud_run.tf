resource "google_cloud_run_v2_service" "scan_service" {
  name     = "scan-service"
  location = var.region

  template {
    service_account = google_service_account.scan_service.email
    max_instance_count = 10
    min_instance_count = 0
    timeout            = "10s"

    scaling {
      min_instance_count = 0
      max_instance_count = 10
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
    timeout            = "10s"

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
    }

    execution_environment = "EXECUTION_ENVIRONMENT_GEN2"
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  ingress = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER_ONLY"
}
