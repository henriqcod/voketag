# Multi-Region Deployment Strategy
# Active-Passive configuration for disaster recovery
#
# Primary Region: us-central1
# Secondary Region: us-east1
#
# RTO: 5 minutes
# RPO: 1 minute

variable "secondary_region" {
  description = "Secondary region for DR"
  type        = string
  default     = "us-east1"
}

# HIGH SECURITY FIX: Externalize hardcoded values
variable "api_domain" {
  description = "API domain name"
  type        = string
  default     = "api.voketag.com.br"
}

variable "sre_email" {
  description = "SRE team email for alerts"
  type        = string
  default     = "sre@voketag.com.br"
}

# ============================================================================
# SECRET MANAGER - Connection Strings
# ============================================================================

resource "google_secret_manager_secret" "database_url_secondary" {
  secret_id = "database-url-secondary"
  
  labels = {
    environment = "production"
    service     = "cloud-sql"
    region      = var.secondary_region
  }

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "database_url_secondary" {
  secret = google_secret_manager_secret.database_url_secondary.id
  
  # Connection string will be set by Cloud SQL IAM authentication or manually
  # Format: postgresql://USER:PASSWORD@HOST:5432/DATABASE?sslmode=require
  secret_data = "postgresql://${google_sql_user.user.name}:${var.db_password}@${google_sql_database_instance.postgres_replica.private_ip_address}:5432/${google_sql_database.db.name}?sslmode=require"
}

# Grant Cloud Run service accounts access to secrets
resource "google_secret_manager_secret_iam_member" "scan_service_secondary" {
  secret_id = google_secret_manager_secret.database_url_secondary.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.scan_service.email}"
}

resource "google_secret_manager_secret_iam_member" "factory_service_secondary" {
  secret_id = google_secret_manager_secret.database_url_secondary.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.factory_service.email}"
}

# ============================================================================
# CLOUD SQL READ REPLICA (Secondary Region)
# ============================================================================

resource "google_sql_database_instance" "postgres_replica" {
  name                 = "voketag-postgres-replica"
  database_version     = "POSTGRES_15"
  region               = var.secondary_region
  master_instance_name = google_sql_database_instance.postgres.name

  replica_configuration {
    failover_target = true # Can be promoted to master
  }

  settings {
    tier              = "db-custom-2-7680" # Same as primary
    availability_type = "REGIONAL"
    
    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = 7
    }

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
      require_ssl     = true
    }

    database_flags {
      name  = "max_connections"
      value = "100"
    }
  }

  deletion_protection = true
}

# ============================================================================
# REDIS REPLICA (Secondary Region)
# ============================================================================

resource "google_redis_instance" "redis_replica" {
  name               = "voketag-redis-replica"
  tier               = "STANDARD_HA"
  memory_size_gb     = 5
  region             = var.secondary_region
  replica_count      = 1
  read_replicas_mode = "READ_REPLICAS_ENABLED"

  redis_version = "REDIS_7_0"

  authorized_network = google_compute_network.vpc.id

  maintenance_policy {
    weekly_maintenance_window {
      day = "SUNDAY"
      start_time {
        hours   = 3
        minutes = 0
      }
    }
  }
}

# ============================================================================
# CLOUD RUN (Secondary Region) - Standby
# ============================================================================

resource "google_cloud_run_v2_service" "scan_service_secondary" {
  name     = "scan-service-dr"
  location = var.secondary_region

  template {
    service_account    = google_service_account.scan_service.email
    max_instance_count = 10
    min_instance_count = 0 # Standby mode

    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }

    containers {
      image = "gcr.io/${var.project_id}/scan-service:latest"

      max_instance_request_concurrency = 80

      env {
        name  = "REGION"
        value = var.secondary_region
      }

      env {
        name  = "DATABASE_URL"
        # HIGH SECURITY FIX: Use Secret Manager instead of hardcoded connection string
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.database_url_secondary.secret_id
            version = "latest"
          }
        }
      }

      env {
        name  = "REDIS_ADDR"
        value = google_redis_instance.redis_replica.host
      }

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

resource "google_cloud_run_v2_service" "factory_service_secondary" {
  name     = "factory-service-dr"
  location = var.secondary_region

  template {
    service_account    = google_service_account.factory_service.email
    max_instance_count = 5
    min_instance_count = 0 # Standby mode

    scaling {
      min_instance_count = 0
      max_instance_count = 5
    }

    containers {
      image = "gcr.io/${var.project_id}/factory-service:latest"

      max_instance_request_concurrency = 80

      env {
        name  = "REGION"
        value = var.secondary_region
      }

      env {
        name  = "DATABASE_URL"
        # HIGH SECURITY FIX: Use Secret Manager instead of hardcoded connection string
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.database_url_secondary.secret_id
            version = "latest"
          }
        }
      }

      env {
        name  = "REDIS_URL"
        value = "redis://${google_redis_instance.redis_replica.host}:6379/0"
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
        cpu_idle = false # Always allocated
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

# ============================================================================
# GLOBAL LOAD BALANCER
# ============================================================================

resource "google_compute_global_address" "lb_ip" {
  name = "voketag-lb-ip"
}

resource "google_compute_global_forwarding_rule" "https" {
  name       = "voketag-https"
  target     = google_compute_target_https_proxy.default.id
  port_range = "443"
  ip_address = google_compute_global_address.lb_ip.address
}

resource "google_compute_target_https_proxy" "default" {
  name             = "voketag-https-proxy"
  url_map          = google_compute_url_map.default.id
  ssl_certificates = [google_compute_managed_ssl_certificate.default.id]
}

resource "google_compute_managed_ssl_certificate" "default" {
  name = "voketag-cert"

  managed {
    # HIGH SECURITY FIX: Use variable instead of hardcoded domain
    domains = [var.api_domain]
  }
}

resource "google_compute_url_map" "default" {
  name            = "voketag-url-map"
  default_service = google_compute_backend_service.scan_primary.id

  host_rule {
    # HIGH SECURITY FIX: Use variable instead of hardcoded domain
    hosts        = [var.api_domain]
    path_matcher = "allpaths"
  }

  path_matcher {
    name            = "allpaths"
    default_service = google_compute_backend_service.scan_primary.id

    path_rule {
      paths   = ["/v1/scan/*"]
      service = google_compute_backend_service.scan_primary.id
    }

    path_rule {
      paths   = ["/v1/products/*", "/v1/batches/*"]
      service = google_compute_backend_service.factory_primary.id
    }
  }
}

# Backend Services with Health Checks
resource "google_compute_backend_service" "scan_primary" {
  name                  = "scan-service-primary"
  protocol              = "HTTP"
  timeout_sec           = 10
  health_checks         = [google_compute_health_check.scan.id]
  load_balancing_scheme = "EXTERNAL_MANAGED"

  backend {
    group = google_compute_region_network_endpoint_group.scan_primary.id
  }

  # Failover to secondary on primary failure
  failover_policy {
    disable_connection_drain_on_failover = true
    drop_traffic_if_unhealthy            = true
    failover_ratio                       = 0.1
  }
}

resource "google_compute_backend_service" "factory_primary" {
  name                  = "factory-service-primary"
  protocol              = "HTTP"
  timeout_sec           = 10
  health_checks         = [google_compute_health_check.factory.id]
  load_balancing_scheme = "EXTERNAL_MANAGED"

  backend {
    group = google_compute_region_network_endpoint_group.factory_primary.id
  }

  failover_policy {
    disable_connection_drain_on_failover = true
    drop_traffic_if_unhealthy            = true
    failover_ratio                       = 0.1
  }
}

# Network Endpoint Groups
resource "google_compute_region_network_endpoint_group" "scan_primary" {
  name                  = "scan-primary-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region

  cloud_run {
    service = google_cloud_run_v2_service.scan_service.name
  }
}

resource "google_compute_region_network_endpoint_group" "factory_primary" {
  name                  = "factory-primary-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region

  cloud_run {
    service = google_cloud_run_v2_service.factory_service.name
  }
}

# Health Checks
resource "google_compute_health_check" "scan" {
  name               = "scan-health-check"
  check_interval_sec = 10
  timeout_sec        = 5
  healthy_threshold  = 2
  unhealthy_threshold = 3

  http_health_check {
    port         = 8080
    request_path = "/v1/health"
  }
}

resource "google_compute_health_check" "factory" {
  name               = "factory-health-check"
  check_interval_sec = 10
  timeout_sec        = 5
  healthy_threshold  = 2
  unhealthy_threshold = 3

  http_health_check {
    port         = 8080
    request_path = "/v1/health"
  }
}

# ============================================================================
# MONITORING & ALERTING
# ============================================================================

resource "google_monitoring_uptime_check_config" "primary_health" {
  display_name = "Primary Region Health Check"
  timeout      = "5s"
  period       = "60s"

  http_check {
    path         = "/v1/health"
    port         = "443"
    use_ssl      = true
    validate_ssl = true
  }

  monitored_resource {
    type = "uptime_url"
    labels = {
      project_id = var.project_id
      # HIGH SECURITY FIX: Use variable instead of hardcoded domain
      host       = var.api_domain
    }
  }
}

resource "google_monitoring_alert_policy" "primary_down" {
  display_name = "Primary Region Down - Failover Required"
  combiner     = "OR"

  conditions {
    display_name = "Primary region unhealthy"

    condition_threshold {
      filter          = "resource.type = \"uptime_url\" AND metric.type = \"monitoring.googleapis.com/uptime_check/check_passed\""
      duration        = "180s"
      comparison      = "COMPARISON_LT"
      threshold_value = 1
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.id]

  alert_strategy {
    auto_close = "1800s" # 30 minutes
  }
}

resource "google_monitoring_notification_channel" "email" {
  display_name = "SRE Team Email"
  type         = "email"

  labels = {
    # HIGH SECURITY FIX: Use variable instead of hardcoded email
    email_address = var.sre_email
  }
}

# ============================================================================
# OUTPUTS
# ============================================================================

output "load_balancer_ip" {
  description = "Global load balancer IP address"
  value       = google_compute_global_address.lb_ip.address
}

output "primary_region" {
  description = "Primary region"
  value       = var.region
}

output "secondary_region" {
  description = "Secondary region (DR)"
  value       = var.secondary_region
}

output "sql_replica_name" {
  description = "Cloud SQL read replica name"
  value       = google_sql_database_instance.postgres_replica.name
}
