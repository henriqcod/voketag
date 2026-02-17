resource "google_redis_instance" "main" {
  name           = "voketag-redis"
  tier           = "BASIC"
  memory_size_gb = 1
  region         = var.region

  authorized_network = google_compute_network.vpc.id

  redis_version     = "REDIS_7_0"
  display_name      = "VokeTag Redis"
  reserved_ip_range = "10.0.0.0/29"
  
  # CRITICAL SECURITY FIX: Enable in-transit encryption (TLS)
  transit_encryption_mode = "SERVER_AUTHENTICATION"
  
  # CRITICAL SECURITY FIX: Enable authentication
  auth_enabled = true
  
  # CRITICAL SECURITY FIX: Customer-Managed Encryption Key for encryption at rest
  customer_managed_key = google_kms_crypto_key.redis_key.id

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

output "redis_host" {
  value       = google_redis_instance.main.host
  description = "Redis host"
}

output "redis_port" {
  value       = google_redis_instance.main.port
  description = "Redis port"
}

output "redis_auth_string" {
  value       = google_redis_instance.main.auth_string
  description = "Redis AUTH string"
  sensitive   = true
}

# CRITICAL SECURITY FIX: Customer-Managed Encryption Key (CMEK) for Redis
resource "google_kms_key_ring" "redis_keyring" {
  name     = "voketag-redis-keyring"
  location = var.region
}

resource "google_kms_crypto_key" "redis_key" {
  name            = "voketag-redis-key"
  key_ring        = google_kms_key_ring.redis_keyring.id
  rotation_period = "7776000s"  # 90 days

  lifecycle {
    prevent_destroy = true
  }
  
  version_template {
    algorithm = "GOOGLE_SYMMETRIC_ENCRYPTION"
  }
}

# Grant Redis service account access to the encryption key
resource "google_kms_crypto_key_iam_member" "redis_crypto_key" {
  crypto_key_id = google_kms_crypto_key.redis_key.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-redis.iam.gserviceaccount.com"
}

# Get project number for service account
data "google_project" "project" {
  project_id = var.project_id
}
