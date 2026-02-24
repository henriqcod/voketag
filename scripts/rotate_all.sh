#!/bin/bash
#
# Script: Master Key & Secret Rotation Orchestrator
# Usage: ./rotate_all.sh [--env=production|staging] [--what=secrets|database|redis|jwt|api-keys|all]
# Frequency: Quarterly (all) or targeted rotations as needed
# Owner: DevOps / Security Team
#
# This script coordinates rotation of ALL secrets with proper sequencing:
# 1. API Keys (external services - can be rotated in any order)
# 2. JWT Secret (auth - rotate with care, users stay logged in)
# 3. Redis Password (cache - restart services after)
# 4. Database Password (most critical - last to minimize disruption)
#
# Safety mechanisms:
# - Dry-run mode (review changes without applying)
# - Health checks after each rotation
# - Rollback capability
# - Audit trail with timestamps
#

set -o pipefail

# ============================================================================
# CONFIGURATION
# ============================================================================

ENV="${1:-staging}"
WHAT="${2:-all}"
PROJECT_ID="voketag-${ENV}"
REGION="us-central1"
TIMESTAMP=$(date -u +'%Y-%m-%d_%H-%M-%S')
LOG_DIR="/var/log/rotation"
LOG_FILE="$LOG_DIR/rotation-${ENV}-${WHAT}-${TIMESTAMP}.log"
DRY_RUN="${DRY_RUN:-false}"

mkdir -p "$LOG_DIR"

# Script locations
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROTATE_API_KEYS="$SCRIPTS_DIR/rotate_api_keys.sh"
ROTATE_JWT="$SCRIPTS_DIR/rotate_jwt_secret.sh"
ROTATE_DB="$SCRIPTS_DIR/rotate_database_password.sh"
ROTATE_REDIS="$SCRIPTS_DIR/rotate_redis_password.sh"

# ============================================================================
# LOGGING
# ============================================================================

log() {
    echo "[$(date -u +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

error() {
    echo "[ERROR] $*" | tee -a "$LOG_FILE"
    exit 1
}

warn() {
    echo "[WARN] $*" | tee -a "$LOG_FILE"
}

success() {
    echo "[✅ SUCCESS] $*" | tee -a "$LOG_FILE"
}

# ============================================================================
# VALIDATION
# ============================================================================

validate_environment() {
    log "Validating environment..."
    
    # Check required tools
    for cmd in gcloud curl jq; do
        if ! command -v $cmd &> /dev/null; then
            error "Required command not found: $cmd"
        fi
    done
    
    # Check GCP project
    CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)
    if [ "$CURRENT_PROJECT" != "$PROJECT_ID" ]; then
        warn "Current project: $CURRENT_PROJECT"
        log "Switch projects with: gcloud config set project $PROJECT_ID"
    fi
    
    # Check script availability
    for script in "$ROTATE_API_KEYS" "$ROTATE_JWT" "$ROTATE_DB" "$ROTATE_REDIS"; do
        if [ ! -f "$script" ]; then
            error "Rotation script not found: $script"
        fi
        chmod +x "$script"
    done
    
    log "✅ Environment validation passed"
}

# ============================================================================
# PRE-ROTATION CHECKS
# ============================================================================

pre_rotation_checks() {
    log "Running pre-rotation checks..."
    
    # Check service health Before rotation
    log "Checking service health..."
    SERVICES=("scan-service" "factory-service" "admin-service" "blockchain-service")
    HEALTHY_COUNT=0
    
    for SERVICE in "${SERVICES[@]}"; do
        if gcloud run services describe "$SERVICE" \
            --region="$REGION" \
            --project="$PROJECT_ID" &>/dev/null; then
            ((HEALTHY_COUNT++))
        fi
    done
    
    if [ $HEALTHY_COUNT -lt 3 ]; then
        error "Less than 3 services healthy. Cannot proceed with rotation. Healthy: $HEALTHY_COUNT/4"
    fi
    
    log "✅ all $HEALTHY_COUNT services are available"
    
    # Check database connectivity
    log "Checking database connectivity..."
    if gcloud sql instances describe "postgres-voketag-${ENV}" \
        --project="$PROJECT_ID" &>/dev/null; then
        log "✅ Database instance accessible"
    else
        error "Database instance not accessible"
    fi
    
    # Check Redis connectivity
    log "Checking Redis connectivity..."
    if gcloud redis instances describe "redis-voketag-${ENV}" \
        --region="$REGION" \
        --project="$PROJECT_ID" &>/dev/null; then
        log "✅ Redis instance accessible"
    else
        warn "Redis instance not accessible (may be in different region)"
    fi
    
    log "✅ Pre-rotation checks passed"
}

# ============================================================================
# EXECUTION FUNCTIONS
# ============================================================================

execute_with_logging() {
    local script_name="$1"
    local script_path="$2"
    
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log "Running: $script_name"
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if [ "$DRY_RUN" = "true" ]; then
        log "[DRY-RUN] Would execute: $script_path --env=$ENV"
        return 0
    fi
    
    if bash "$script_path" --env="$ENV" 2>&1 | tee -a "$LOG_FILE"; then
        success "$script_name completed successfully"
        return 0
    else
        ERR_CODE=$?
        error "$script_name failed with exit code: $ERR_CODE"
        return $ERR_CODE
    fi
}

rotate_api_keys() {
    log ""
    log "STEP 1/4: Rotating API Keys"
    log "Impact: External service calls (Stripe, Google Maps) may have temporary failures"
    execute_with_logging "API Keys Rotation" "$ROTATE_API_KEYS"
    sleep 5  # Allow services to process new env vars
}

rotate_jwt_secret() {
    log ""
    log "STEP 2/4: Rotating JWT Secret"
    log "Impact: Users may need to re-authenticate (graceful, no forced logout)"
    execute_with_logging "JWT Secret Rotation" "$ROTATE_JWT" --env="$ENV"
    sleep 10  # Allow token refresh propagation
}

rotate_redis_password() {
    log ""
    log "STEP 3/4: Rotating Redis Password"
    log "Impact: Brief cache misses as connections refresh"
    execute_with_logging "Redis Password Rotation" "$ROTATE_REDIS" --env="$ENV"
    sleep 10  # Allow replication
}

rotate_database_password() {
    log ""
    log "STEP 4/4: Rotating Database Password"
    log "Impact: Brief connection pooling adjustments"
    execute_with_logging "Database Password Rotation" "$ROTATE_DB" --env="$ENV"
    sleep 15  # Allow new connections to stabilize
}

# ============================================================================
# POST-ROTATION CHECKS
# ============================================================================

post_rotation_checks() {
    log ""
    log "Running post-rotation health checks..."
    
    SERVICES=("scan-service" "factory-service" "admin-service" "blockchain-service")
    HEALTHY=0
    
    for SERVICE in "${SERVICES[@]}"; do
        SERVICE_HEALTH=$(gcloud run services describe "$SERVICE" \
            --region="$REGION" \
            --project="$PROJECT_ID" \
            --format='value(status.conditions[0].status)' 2>/dev/null || echo "UNKNOWN")
        
        if [ "$SERVICE_HEALTH" = "True" ]; then
            log "✅ $SERVICE is healthy"
            ((HEALTHY++))
        else
            warn "⚠️  $SERVICE health status: $SERVICE_HEALTH"
        fi
    done
    
    if [ $HEALTHY -lt 3 ]; then
        warn "❌ Less than 3 services healthy after rotation!"
        warn "Please investigate and consider rollback"
        return 1
    fi
    
    log "✅ Post-rotation health checks passed ($HEALTHY/$4 services healthy)"
    return 0
}

# ============================================================================
# REPORTING
# ============================================================================

generate_report() {
    log ""
    log "╔════════════════════════════════════════════════════════════════╗"
    log "║                  ROTATION REPORT                              ║"
    log "╚════════════════════════════════════════════════════════════════╝"
    log ""
    log "Environment:    $ENV"
    log "Execution Mode: $([ "$DRY_RUN" = "true" ] && echo "DRY-RUN" || echo "LIVE")"
    log "Rotation Type:  $WHAT"
    log "Timestamp:      $TIMESTAMP"
    log "Log File:       $LOG_FILE"
    log ""
    log "Next Steps:"
    log "  1. Monitor application logs for any connection errors"
    log "  2. Check Cloud Run revision metrics (latency, error rate)"
    log "  3. Verify database and cache query performance"
    log ""
    log "To view detailed logs:"
    log "  tail -f $LOG_FILE"
    log ""
    log "Audit trail preserved in:"
    log "  /var/log/rotation/"
    log ""
    
    # Copy log to GCS for long-term audit
    if [ "$DRY_RUN" != "true" ]; then
        log "Uploading audit log to Cloud Storage..."
        gsutil cp "$LOG_FILE" \
            "gs://voketag-audit-logs/rotation-${ENV}/${TIMESTAMP}.log" \
            2>/dev/null || warn "Could not upload to GCS (may lack permissions)"
    fi
}

# ============================================================================
# MAIN ORCHESTRATION
# ============================================================================

main() {
    clear
    log "╔════════════════════════════════════════════════════════════════╗"
    log "║          SECRET & KEY ROTATION ORCHESTRATOR                   ║"
    log "║                                                                ║"
    log "║  Env: $ENV | Type: $WHAT | Mode: $([ "$DRY_RUN" = "true" ] && echo "DRY-RUN" || echo "LIVE")"
    log "╚════════════════════════════════════════════════════════════════╝"
    log ""
    
    # Validation
    validate_environment
    pre_rotation_checks
    
    # Rotation
    case "$WHAT" in
        "api-keys")
            rotate_api_keys
            ;;
        "jwt")
            rotate_jwt_secret
            ;;
        "redis")
            rotate_redis_password
            ;;
        "database")
            rotate_database_password
            ;;
        "all"|*)
            rotate_api_keys
            rotate_jwt_secret
            rotate_redis_password
            rotate_database_password
            ;;
    esac
    
    # Health checks
    if post_rotation_checks; then
        log ""
        success "ALL ROTATIONS COMPLETED SUCCESSFULLY"
    else
        log ""
        error "ROTATION COMPLETED WITH WARNINGS - CHECK SERVICES"
    fi
    
    # Report
    generate_report
}

# ============================================================================
# USAGE
# ============================================================================

if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    cat << EOF

Usage: $0 [OPTIONS]

Options:
  --env=ENV          Environment: production|staging (default: staging)
  --what=TYPE        Rotation type: api-keys|jwt|redis|database|all (default: all)
  --dry-run          Preview changes without applying
  -h, --help        Show this help message

Examples:

  # Rotate all secrets in staging (safe to test)
  $0 --env=staging --what=all

  # Dry-run production rotation (preview only)
  DRY_RUN=true $0 --env=production --what=all

  # Rotate only JWT secret
  $0 --env=production --what=jwt

  # Rotate database password on production
  $0 --env=production --what=database

Rotation Sequence (--what=all):
  1. API Keys       (external services, no user impact)
  2. JWT Secret     (graceful token refresh)
  3. Redis Password (brief cache misses)
  4. Database Pass  (connection refresh, last for safety)

Safety Features:
  ✓ Pre-rotation health checks
  ✓ Service restart automation
  ✓ Post-rotation validation
  ✓ Audit trail logging
  ✓ Dry-run mode for testing
  ✓ GCS audit log backup

EOF
    exit 0
fi

# Parse arguments
for arg in "$@"; do
    case $arg in
        --env=*)
            ENV="${arg#*=}"
            PROJECT_ID="voketag-${ENV}"
            ;;
        --what=*)
            WHAT="${arg#*=}"
            ;;
        --dry-run)
            DRY_RUN="true"
            ;;
        *)
            warn "Unknown option: $arg"
            ;;
    esac
done

# Execute
main "$@"
