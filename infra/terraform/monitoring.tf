# HIGH SECURITY FIX: Cloud Monitoring and Alerting
# Monitors critical infrastructure health and sends alerts to SRE team

# Notification channel for alerts (email)
resource "google_monitoring_notification_channel" "email" {
  display_name = "VokeTag SRE Email"
  type         = "email"
  
  labels = {
    email_address = var.sre_email
  }
}

# Notification channel for PagerDuty (production incidents)
resource "google_monitoring_notification_channel" "pagerduty" {
  display_name = "VokeTag PagerDuty"
  type         = "pagerduty"
  
  labels = {
    service_key = var.pagerduty_service_key
  }
  
  enabled = var.env == "production"
}

# Alert: Cloud Run Service Down
resource "google_monitoring_alert_policy" "cloud_run_down" {
  display_name = "Cloud Run Service Down"
  combiner     = "OR"
  
  conditions {
    display_name = "Cloud Run service is not responding"
    
    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/request_count\""
      duration        = "300s"  # 5 minutes
      comparison      = "COMPARISON_LT"
      threshold_value = 1
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }
  
  notification_channels = [
    google_monitoring_notification_channel.email.id,
    google_monitoring_notification_channel.pagerduty.id,
  ]
  
  alert_strategy {
    auto_close = "1800s"  # Auto-close after 30 minutes if resolved
  }
}

# Alert: High Error Rate
resource "google_monitoring_alert_policy" "high_error_rate" {
  display_name = "High Error Rate (5xx)"
  combiner     = "OR"
  
  conditions {
    display_name = "5xx error rate > 5%"
    
    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/request_count\" AND metric.label.response_code_class=\"5xx\""
      duration        = "180s"  # 3 minutes
      comparison      = "COMPARISON_GT"
      threshold_value = 0.05  # 5%
      
      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_SUM"
        group_by_fields      = ["resource.service_name"]
      }
    }
  }
  
  notification_channels = [
    google_monitoring_notification_channel.email.id,
    google_monitoring_notification_channel.pagerduty.id,
  ]
}

# Alert: Redis High Memory Usage
resource "google_monitoring_alert_policy" "redis_memory" {
  display_name = "Redis High Memory Usage"
  combiner     = "OR"
  
  conditions {
    display_name = "Memory usage > 80%"
    
    condition_threshold {
      filter          = "resource.type=\"redis_instance\" AND metric.type=\"redis.googleapis.com/stats/memory/usage_ratio\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.8
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }
  
  notification_channels = [
    google_monitoring_notification_channel.email.id,
  ]
}

# Alert: Cloud SQL High CPU
resource "google_monitoring_alert_policy" "cloudsql_cpu" {
  display_name = "Cloud SQL High CPU"
  combiner     = "OR"
  
  conditions {
    display_name = "CPU utilization > 80%"
    
    condition_threshold {
      filter          = "resource.type=\"cloudsql_database\" AND metric.type=\"cloudsql.googleapis.com/database/cpu/utilization\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.8
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }
  
  notification_channels = [
    google_monitoring_notification_channel.email.id,
  ]
}

# Alert: Cloud SQL High Connection Count
resource "google_monitoring_alert_policy" "cloudsql_connections" {
  display_name = "Cloud SQL High Connection Count"
  combiner     = "OR"
  
  conditions {
    display_name = "Active connections > 80"
    
    condition_threshold {
      filter          = "resource.type=\"cloudsql_database\" AND metric.type=\"cloudsql.googleapis.com/database/postgresql/num_backends\""
      duration        = "180s"
      comparison      = "COMPARISON_GT"
      threshold_value = 80
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }
  
  notification_channels = [
    google_monitoring_notification_channel.email.id,
  ]
}

# Alert: Cloud Run High Latency
resource "google_monitoring_alert_policy" "high_latency" {
  display_name = "Cloud Run High Latency"
  combiner     = "OR"
  
  conditions {
    display_name = "P95 latency > 1000ms"
    
    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/request_latencies\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 1000  # 1 second
      
      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_DELTA"
        cross_series_reducer = "REDUCE_PERCENTILE_95"
        group_by_fields      = ["resource.service_name"]
      }
    }
  }
  
  notification_channels = [
    google_monitoring_notification_channel.email.id,
  ]
}

# Alert: Cloud Run Container Instance Count
resource "google_monitoring_alert_policy" "instance_count" {
  display_name = "Cloud Run High Instance Count"
  combiner     = "OR"
  
  conditions {
    display_name = "Active instances > 80% of max"
    
    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/container/instance_count\""
      duration        = "180s"
      comparison      = "COMPARISON_GT"
      threshold_value = 8  # 80% of max (10)
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MAX"
      }
    }
  }
  
  notification_channels = [
    google_monitoring_notification_channel.email.id,
  ]
}

# Dashboard for monitoring
resource "google_monitoring_dashboard" "main" {
  dashboard_json = jsonencode({
    displayName = "VokeTag Production Dashboard"
    
    gridLayout = {
      widgets = [
        {
          title = "Cloud Run Request Rate"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/request_count\""
                  aggregation = {
                    alignmentPeriod  = "60s"
                    perSeriesAligner = "ALIGN_RATE"
                  }
                }
              }
            }]
          }
        },
        {
          title = "Error Rate (5xx)"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/request_count\" AND metric.label.response_code_class=\"5xx\""
                  aggregation = {
                    alignmentPeriod  = "60s"
                    perSeriesAligner = "ALIGN_RATE"
                  }
                }
              }
            }]
          }
        },
        {
          title = "Redis Memory Usage"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type=\"redis_instance\" AND metric.type=\"redis.googleapis.com/stats/memory/usage_ratio\""
                  aggregation = {
                    alignmentPeriod  = "60s"
                    perSeriesAligner = "ALIGN_MEAN"
                  }
                }
              }
            }]
          }
        },
        {
          title = "Cloud SQL CPU"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type=\"cloudsql_database\" AND metric.type=\"cloudsql.googleapis.com/database/cpu/utilization\""
                  aggregation = {
                    alignmentPeriod  = "60s"
                    perSeriesAligner = "ALIGN_MEAN"
                  }
                }
              }
            }]
          }
        }
      ]
    }
  })
}

# Variables for monitoring
variable "pagerduty_service_key" {
  type        = string
  description = "PagerDuty service integration key"
  sensitive   = true
  default     = ""
}
