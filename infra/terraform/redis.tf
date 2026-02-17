resource "google_redis_instance" "main" {
  name           = "voketag-redis"
  tier           = "BASIC"
  memory_size_gb = 1
  region         = var.region

  authorized_network = google_compute_network.vpc.id

  redis_version     = "REDIS_7_0"
  display_name      = "VokeTag Redis"
  reserved_ip_range = "10.0.0.0/29"

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
