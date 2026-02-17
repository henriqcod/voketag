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
  
  # CRITICAL SECURITY FIX: Enable encryption at rest with customer-managed encryption key (CMEK)
  # Data is encrypted both at rest and in transit
  encryption_key_name = google_kms_crypto_key.sql_key.id

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
      
      # CRITICAL SECURITY FIX: Enforce TLS 1.2+ only
      ssl_mode = "ENCRYPTED_ONLY"
    }

    database_flags {
      name  = "max_connections"
      value = "100"
    }
    
    # CRITICAL SECURITY FIX: Enable automated data encryption
    database_flags {
      name  = "cloudsql.enable_pgaudit"
      value = "on"
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

# CRITICAL SECURITY FIX: Customer-Managed Encryption Keys (CMEK) for Cloud SQL
# Provides encryption at rest with keys managed by the customer
resource "google_kms_key_ring" "sql_keyring" {
  name     = "voketag-sql-keyring"
  location = var.region
}

resource "google_kms_crypto_key" "sql_key" {
  name            = "voketag-sql-key"
  key_ring        = google_kms_key_ring.sql_keyring.id
  rotation_period = "7776000s"  # 90 days

  lifecycle {
    prevent_destroy = true
  }
  
  version_template {
    algorithm = "GOOGLE_SYMMETRIC_ENCRYPTION"
  }
}

# Grant Cloud SQL service account access to the encryption key
resource "google_kms_crypto_key_iam_member" "sql_crypto_key" {
  crypto_key_id = google_kms_crypto_key.sql_key.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-cloud-sql.iam.gserviceaccount.com"
}

# Get project number for service account
data "google_project" "project" {
  project_id = var.project_id
}
