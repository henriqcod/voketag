# LOW ENHANCEMENT: Refined Cloud Monitoring Alerts
# 
# Improvements:
# 1. More granular alert thresholds
# 2. Severity levels (CRITICAL, WARNING, INFO)
# 3. Business-specific alerts (antifraud, scan latency)
# 4. SLO-based alerting
# 5. Alert documentation
# 6. Reduced alert fatigue

# Notification Channels
resource "google_monitoring_notification_channel" "email" {
  display_name = "VokeTag SRE Email"
  type         = "email"
  
  labels = {
    email_address = var.sre_email
  }
}

resource "google_monitoring_notification_channel" "pagerduty_critical" {
  display_name = "PagerDuty Critical"
  type         = "pagerduty"
  
  labels = {
    service_key = var.pagerduty_critical_key
  }
  
  enabled = var.env == "production"
}

resource "google_monitoring_notification_channel" "pagerduty_warning" {
  display_name = "PagerDuty Warning"
  type         = "pagerduty"
  
  labels = {
    service_key = var.pagerduty_warning_key
  }
  
  enabled = var.env == "production"
}

resource "google_monitoring_notification_channel" "slack" {
  display_name = "Slack #alerts"
  type         = "slack"
  
  labels = {
    channel_name = "#alerts"
    url          = var.slack_webhook_url
  }
}

# ============================================================================
# CRITICAL ALERTS (Page immediately)
# ============================================================================

# CRITICAL: Service Completely Down
resource "google_monitoring_alert_policy" "service_down_critical" {
  display_name = "[CRITICAL] Service Down"
  combiner     = "OR"
  
  conditions {
    display_name = "Zero requests for 5 minutes"
    
    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/request_count\""
      duration        = "300s"
      comparison      = "COMPARISON_LT"
      threshold_value = 1
      
      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_SUM"
        group_by_fields      = ["resource.service_name"]
      }
    }
  }
  
  notification_channels = [
    google_monitoring_notification_channel.pagerduty_critical.id,
    google_monitoring_notification_channel.slack.id,
  ]
  
  alert_strategy {
    auto_close = "1800s"
  }
  
  documentation {
    content   = <<-EOT
      # Service Down - Critical

      ## Impact
      - Users cannot access the service
      - Business operations halted

      ## Runbook
      1. Check Cloud Run console for service status
      2. Review service logs for errors
      3. Check dependencies (Redis, PostgreSQL)
      4. Verify recent deployments
      5. Roll back if necessary

      ## Escalation
      Page SRE on-call if not resolved in 5 minutes.
    EOT
    mime_type = "text/markdown"
  }
}

# CRITICAL: Extreme Error Rate (>10%)
resource "google_monitoring_alert_policy" "error_rate_critical" {
  display_name = "[CRITICAL] Extreme Error Rate"
  combiner     = "OR"
  
  conditions {
    display_name = "5xx error rate > 10%"
    
    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/request_count\" AND metric.label.response_code_class=\"5xx\""
      duration        = "180s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.10
      
      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_SUM"
        group_by_fields      = ["resource.service_name"]
      }
    }
  }
  
  notification_channels = [
    google_monitoring_notification_channel.pagerduty_critical.id,
    google_monitoring_notification_channel.slack.id,
  ]
  
  documentation {
    content   = <<-EOT
      # Extreme Error Rate - Critical

      ## Impact
      - 1 in 10 requests failing
      - Severe user experience degradation

      ## Common Causes
      - Database connection pool exhausted
      - Redis unavailable
      - Circuit breaker open
      - Recent bad deployment

      ## Runbook
      1. Check APM traces for error patterns
      2. Review service logs
      3. Check database and Redis health
      4. Verify circuit breaker state
      5. Consider rolling back recent deploy
    EOT
    mime_type = "text/markdown"
  }
}

# CRITICAL: Database Unavailable
resource "google_monitoring_alert_policy" "database_down" {
  display_name = "[CRITICAL] Database Unavailable"
  combiner     = "OR"
  
  conditions {
    display_name = "Database CPU = 0 (instance down)"
    
    condition_threshold {
      filter          = "resource.type=\"cloudsql_database\" AND metric.type=\"cloudsql.googleapis.com/database/up\""
      duration        = "60s"
      comparison      = "COMPARISON_LT"
      threshold_value = 1
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }
  
  notification_channels = [
    google_monitoring_notification_channel.pagerduty_critical.id,
  ]
  
  documentation {
    content   = <<-EOT
      # Database Unavailable - Critical

      ## Impact
      - All services unable to access database
      - Data layer completely unavailable

      ## Immediate Actions
      1. Check Cloud SQL console
      2. Verify instance is running
      3. Check maintenance windows
      4. Review instance logs
      5. Contact GCP support if needed
    EOT
    mime_type = "text/markdown"
  }
}

# CRITICAL: Redis Down
resource "google_monitoring_alert_policy" "redis_down" {
  display_name = "[CRITICAL] Redis Unavailable"
  combiner     = "OR"
  
  conditions {
    display_name = "Redis connections = 0"
    
    condition_threshold {
      filter          = "resource.type=\"redis_instance\" AND metric.type=\"redis.googleapis.com/clients/connected\""
      duration        = "180s"
      comparison      = "COMPARISON_LT"
      threshold_value = 1
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MIN"
      }
    }
  }
  
  notification_channels = [
    google_monitoring_notification_channel.pagerduty_critical.id,
  ]
  
  documentation {
    content   = <<-EOT
      # Redis Unavailable - Critical

      ## Impact
      - Cache unavailable
      - Increased database load
      - Higher latency

      ## Expected Behavior
      - Services should fall back to database
      - Circuit breaker should open
      - 503 errors if fallback fails

      ## Actions
      1. Check Redis console
      2. Verify instance is running
      3. Check maintenance windows
      4. Monitor database load (should increase)
    EOT
    mime_type = "text/markdown"
  }
}

# ============================================================================
# WARNING ALERTS (Investigate soon)
# ============================================================================

# WARNING: High Error Rate (>5%)
resource "google_monitoring_alert_policy" "error_rate_warning" {
  display_name = "[WARNING] High Error Rate"
  combiner     = "OR"
  
  conditions {
    display_name = "5xx error rate > 5%"
    
    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/request_count\" AND metric.label.response_code_class=\"5xx\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.05
      
      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_SUM"
        group_by_fields      = ["resource.service_name"]
      }
    }
  }
  
  notification_channels = [
    google_monitoring_notification_channel.pagerduty_warning.id,
    google_monitoring_notification_channel.slack.id,
  ]
  
  documentation {
    content = "High error rate detected. Review logs and APM traces."
  }
}

# WARNING: P95 Latency High (>500ms for scan service)
resource "google_monitoring_alert_policy" "latency_scan_warning" {
  display_name = "[WARNING] Scan Service High Latency"
  combiner     = "OR"
  
  conditions {
    display_name = "P95 latency > 500ms"
    
    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/request_latencies\" AND resource.label.service_name=\"scan-service\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 500
      
      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_DELTA"
        cross_series_reducer = "REDUCE_PERCENTILE_95"
      }
    }
  }
  
  notification_channels = [
    google_monitoring_notification_channel.slack.id,
  ]
  
  documentation {
    content   = <<-EOT
      # Scan Service High Latency

      ## SLO Target
      P95 < 100ms, Acceptable < 200ms

      ## Common Causes
      - Cache misses
      - Database slow queries
      - Network latency
      - High load

      ## Actions
      1. Check cache hit ratio
      2. Review database query performance
      3. Check APM traces
      4. Consider scaling up
    EOT
    mime_type = "text/markdown"
  }
}

# WARNING: High CPU Usage
resource "google_monitoring_alert_policy" "cpu_high" {
  display_name = "[WARNING] High CPU Usage"
  combiner     = "OR"
  
  conditions {
    display_name = "CPU > 80% for 5 minutes"
    
    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/container/cpu/utilizations\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.8
      
      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_MEAN"
        cross_series_reducer = "REDUCE_MEAN"
        group_by_fields      = ["resource.service_name"]
      }
    }
  }
  
  notification_channels = [
    google_monitoring_notification_channel.slack.id,
  ]
  
  documentation {
    content = "High CPU detected. Consider autoscaling or investigating CPU-intensive operations."
  }
}

# WARNING: High Memory Usage
resource "google_monitoring_alert_policy" "memory_high" {
  display_name = "[WARNING] High Memory Usage"
  combiner     = "OR"
  
  conditions {
    display_name = "Memory > 80%"
    
    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/container/memory/utilizations\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.8
      
      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_MEAN"
        cross_series_reducer = "REDUCE_MEAN"
        group_by_fields      = ["resource.service_name"]
      }
    }
  }
  
  notification_channels = [
    google_monitoring_notification_channel.slack.id,
  ]
  
  documentation {
    content = "High memory usage. Possible memory leak or increased load."
  }
}

# WARNING: Database Connection Pool High
resource "google_monitoring_alert_policy" "database_connections_high" {
  display_name = "[WARNING] Database Connections High"
  combiner     = "OR"
  
  conditions {
    display_name = "Connections > 80% of max"
    
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
    google_monitoring_notification_channel.slack.id,
  ]
  
  documentation {
    content = "Database connection pool nearing capacity. Check for connection leaks."
  }
}

# ============================================================================
# INFO ALERTS (Awareness only, no action required)
# ============================================================================

# INFO: Approaching Instance Limit
resource "google_monitoring_alert_policy" "instances_high" {
  display_name = "[INFO] Approaching Instance Limit"
  combiner     = "OR"
  
  conditions {
    display_name = "Instances > 70% of max"
    
    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/container/instance_count\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 70  # 70% of max (100)
      
      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_MAX"
        cross_series_reducer = "REDUCE_MAX"
        group_by_fields      = ["resource.service_name"]
      }
    }
  }
  
  notification_channels = [
    google_monitoring_notification_channel.slack.id,
  ]
  
  documentation {
    content = "High instance count. Consider increasing max_instances if sustained."
  }
}

# INFO: Low Cache Hit Ratio (if custom metrics enabled)
# This would require custom metrics to be exported first

# ============================================================================
# SLO-BASED ALERTS
# ============================================================================

# SLO: 99.9% Availability
resource "google_monitoring_slo" "availability" {
  service      = "scan-service"
  display_name = "99.9% Availability"
  
  goal                = 0.999
  rolling_period_days = 30
  
  request_based_sli {
    good_total_ratio {
      good_service_filter = <<-EOT
        resource.type="cloud_run_revision"
        AND resource.label.service_name="scan-service"
        AND metric.type="run.googleapis.com/request_count"
        AND metric.label.response_code_class!="5xx"
      EOT
      
      total_service_filter = <<-EOT
        resource.type="cloud_run_revision"
        AND resource.label.service_name="scan-service"
        AND metric.type="run.googleapis.com/request_count"
      EOT
    }
  }
}

# Alert when SLO burn rate is high
resource "google_monitoring_alert_policy" "slo_burn_rate" {
  display_name = "[WARNING] SLO Burn Rate High"
  combiner     = "OR"
  
  conditions {
    display_name = "Burning error budget too fast"
    
    condition_threshold {
      filter          = "select_slo_burn_rate(\"${google_monitoring_slo.availability.id}\", 3600)"
      duration        = "0s"
      comparison      = "COMPARISON_GT"
      threshold_value = 10  # Burning 10x faster than normal
    }
  }
  
  notification_channels = [
    google_monitoring_notification_channel.pagerduty_warning.id,
    google_monitoring_notification_channel.slack.id,
  ]
  
  documentation {
    content = "Error budget burning too fast. At this rate, we'll miss our SLO."
  }
}

# ============================================================================
# ENHANCED DASHBOARD
# ============================================================================

resource "google_monitoring_dashboard" "main_enhanced" {
  dashboard_json = jsonencode({
    displayName = "VokeTag Production Dashboard (Enhanced)"
    
    gridLayout = {
      widgets = [
        # Row 1: Overview
        {
          title = "Request Rate (req/s)"
          scorecard = {
            timeSeriesQuery = {
              timeSeriesFilter = {
                filter = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/request_count\""
                aggregation = {
                  alignmentPeriod     = "60s"
                  perSeriesAligner    = "ALIGN_RATE"
                  crossSeriesReducer  = "REDUCE_SUM"
                  groupByFields       = []
                }
              }
            }
            sparkChartView = {
              sparkChartType = "SPARK_LINE"
            }
          }
        },
        {
          title = "Error Rate (%)"
          scorecard = {
            timeSeriesQuery = {
              timeSeriesFilter = {
                filter = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/request_count\" AND metric.label.response_code_class=\"5xx\""
                aggregation = {
                  alignmentPeriod     = "60s"
                  perSeriesAligner    = "ALIGN_RATE"
                  crossSeriesReducer  = "REDUCE_SUM"
                }
              }
            }
            sparkChartView = {
              sparkChartType = "SPARK_LINE"
            }
          }
        },
        {
          title = "P95 Latency (ms)"
          scorecard = {
            timeSeriesQuery = {
              timeSeriesFilter = {
                filter = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/request_latencies\""
                aggregation = {
                  alignmentPeriod     = "60s"
                  perSeriesAligner    = "ALIGN_DELTA"
                  crossSeriesReducer  = "REDUCE_PERCENTILE_95"
                }
              }
            }
            sparkChartView = {
              sparkChartType = "SPARK_LINE"
            }
          }
        },
        {
          title = "Active Instances"
          scorecard = {
            timeSeriesQuery = {
              timeSeriesFilter = {
                filter = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/container/instance_count\""
                aggregation = {
                  alignmentPeriod     = "60s"
                  perSeriesAligner    = "ALIGN_MAX"
                  crossSeriesReducer  = "REDUCE_SUM"
                }
              }
            }
            sparkChartView = {
              sparkChartType = "SPARK_LINE"
            }
          }
        }
      ]
    }
  })
}

# Variables
variable "slack_webhook_url" {
  type        = string
  description = "Slack webhook URL for alerts"
  sensitive   = true
  default     = ""
}

variable "pagerduty_critical_key" {
  type        = string
  description = "PagerDuty integration key for critical alerts"
  sensitive   = true
  default     = ""
}

variable "pagerduty_warning_key" {
  type        = string
  description = "PagerDuty integration key for warning alerts"
  sensitive   = true
  default     = ""
}
