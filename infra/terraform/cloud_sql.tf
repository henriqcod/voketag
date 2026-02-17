variable "db_name" {
  type    = string
  default = "voketag"
}

variable "db_user" {
  type    = string
  default = "voketag"
}

variable "db_password" {
  type      = string
  sensitive = true
}

resource "google_sql_database_instance" "main" {
  depends_on       = [google_service_networking_connection.private_vpc_connection]
  name             = "voketag-db"
  database_version = "POSTGRES_16"
  region           = var.region

  settings {
    tier = "db-f1-micro"

    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = 7
      backup_retention_settings {
        retained_backups = 7
      }
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

    insights_config {
      query_insights_enabled  = true
      query_plans_per_minute  = 5
      query_string_length     = 1024
      record_application_tags = true
      record_client_address   = true
    }
  }

  # HIGH SECURITY FIX: Enable deletion protection to prevent accidental deletion
  # This is a critical database and should never be deleted accidentally
  # To delete: set this to false, apply, then destroy
  deletion_protection = true
}

resource "google_sql_database" "db" {
  name     = var.db_name
  instance = google_sql_database_instance.main.name
}

resource "google_sql_user" "user" {
  name     = var.db_user
  instance = google_sql_database_instance.main.name
  password = var.db_password
}

resource "google_compute_network" "vpc" {
  name                    = "voketag-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_global_address" "private_ip_range" {
  name          = "voketag-private-ip"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_range.name]
}
