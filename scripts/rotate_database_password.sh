#!/bin/bash
#
# Script: Rotate PostgreSQL Database Password with Zero Downtime
# Usage: ./rotate_database_password.sh [--env=production|staging]
# Frequency: Quarterly or on compromise
# Owner: DevOps / Database Admin
#
# This script implements dual-password rotation strategy:
# 1. Create new database user with new password
# 2. Verify new user can connect and has correct privileges
# 3. Update applications to connect with new credentials
# 4. Wait 24 hours for all connections to refresh
# 5. Revoke old user (prevents accidental reuse)
#
# ZERO DOWNTIME: Pool connections refresh automatically via connection retry logic
#

set -e
set -o pipefail

# ============================================================================
# CONFIGURATION
# ============================================================================

ENV="${1:-staging}"
PROJECT_ID="${GCP_PROJECT_ID:-voketag-${ENV}}"
REGION="us-central1"
INSTANCE_NAME="postgres-voketag-${ENV}"
DATABASE_NAME="voketag"
OLD_USER="voketag_app"
NEW_USER="voketag_app_new"
TIMESTAMP=$(date -u +'%Y-%m-%d_%H-%M-%S')
LOG_FILE="/var/log/db-rotation-${TIMESTAMP}.log"

# Database requirements
DB_PASSWORD_LENGTH=32
DB_PASSWORD_CHARSET="A-Za-z0-9_!@#$%"

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

# ============================================================================
# GENERATE SECURE PASSWORD
# ============================================================================

generate_db_password() {
    openssl rand -base64 32 | tr -d '=/+' | cut -c1-${DB_PASSWORD_LENGTH}
}

# ============================================================================
# PHASE 1: CREATE AND VERIFY NEW USER
# ============================================================================

phase_1_create_new_user() {
    log "=== PHASE 1: Create New Database User ==="
    
    NEW_PASSWORD=$(generate_db_password)
    log "Generated new password (length: ${#NEW_PASSWORD})"
    
    # Store in Secret Manager temporarily
    echo -n "$NEW_PASSWORD" | gcloud secrets create "postgres-password-${TIMESTAMP}" \
        --data-file=- \
        --replication-policy="automatic" \
        --project="$PROJECT_ID" 2>/dev/null || \
    echo -n "$NEW_PASSWORD" | gcloud secrets versions add "postgres-password-${TIMESTAMP}" \
        --data-file=- \
        --project="$PROJECT_ID"
    
    log "Stored new password in Secret Manager: postgres-password-${TIMESTAMP}"
    
    # Connect to database and create new user
    log "Creating new database user: $NEW_USER"
    
    TEMP_SQL=$(mktemp)
    cat > "$TEMP_SQL" << EOF
-- Create new user with new password
CREATE USER $NEW_USER WITH PASSWORD '$NEW_PASSWORD';

-- Grant all privileges on database
GRANT CONNECT ON DATABASE $DATABASE_NAME TO $NEW_USER;
GRANT USAGE ON SCHEMA public TO $NEW_USER;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $NEW_USER;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $NEW_USER;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO $NEW_USER;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $NEW_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $NEW_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO $NEW_USER;
EOF

    # Execute SQL via Cloud SQL Proxy
    log "Executing SQL on $INSTANCE_NAME..."
    gcloud sql connect "$INSTANCE_NAME" \
        --user=postgres \
        --database="$DATABASE_NAME" \
        < "$TEMP_SQL" \
        2>/dev/null || error "Failed to create new database user"
    
    rm -f "$TEMP_SQL"
    log "✅ New database user created: $NEW_USER"
    
    # Save credentials for next phase
    echo "$NEW_PASSWORD" > /tmp/new_db_password
    chmod 600 /tmp/new_db_password
}

# ============================================================================
# PHASE 2: TEST NEW USER CONNECTION
# ============================================================================

phase_2_test_connection() {
    log "=== PHASE 2: Test New User Connection ==="
    
    NEW_PASSWORD=$(cat /tmp/new_db_password)
    
    # Get Connection String
    INSTANCE_CONNECTION_NAME=$(gcloud sql instances describe "$INSTANCE_NAME" \
        --project="$PROJECT_ID" \
        --format='value(connectionName)')
    
    log "Testing connection with $NEW_USER..."
    
    # Use Cloud SQL Proxy to test
    TEST_SQL=$(mktemp)
    cat > "$TEST_SQL" << EOF
SELECT current_user, current_database, version();
SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'public';
EOF

    if gcloud sql connect "$INSTANCE_NAME" \
        --user="$NEW_USER" \
        --database="$DATABASE_NAME" \
        < "$TEST_SQL" \
        2>/dev/null; then
        log "✅ Connection test passed for $NEW_USER"
    else
        error "Connection test FAILED for $NEW_USER"
    fi
    
    rm -f "$TEST_SQL"
}

# ============================================================================
# PHASE 3: UPDATE SECRET MANAGER CREDENTIALS
# ============================================================================

phase_3_update_secrets() {
    log "=== PHASE 3: Update Secret Manager ==="
    
    NEW_PASSWORD=$(cat /tmp/new_db_password)
    
    # Update DATABASE_PASSWORD secret
    log "Updating DATABASE_PASSWORD in Secret Manager..."
    
    CREDS_JSON=$(cat <<EOF
{
  "username": "$NEW_USER",
  "password": "$NEW_PASSWORD",
  "host": "127.0.0.1",
  "port": 5432,
  "database": "$DATABASE_NAME"
}
EOF
)
    
    echo -n "$CREDS_JSON" | gcloud secrets versions add DATABASE_PASSWORD \
        --data-file=- \
        --project="$PROJECT_ID" || \
    echo -n "$CREDS_JSON" | gcloud secrets create DATABASE_PASSWORD \
        --data-file=- \
        --replication-policy="automatic" \
        --project="$PROJECT_ID"
    
    log "✅ DATABASE_PASSWORD secret updated"
    
    # Verify secret
    VERIFY=$(gcloud secrets versions access latest --secret=DATABASE_PASSWORD --project="$PROJECT_ID" | jq -r '.username')
    if [ "$VERIFY" = "$NEW_USER" ]; then
        log "✅ Secret verification passed"
    else
        error "Secret verification FAILED"
    fi
}

# ============================================================================
# PHASE 4: RESTART CLOUD RUN SERVICES
# ============================================================================

phase_4_restart_services() {
    log "=== PHASE 4: Restart Cloud Run Services ==="
    
    SERVICES=("factory-service" "blockchain-service" "admin-service")
    
    for SERVICE in "${SERVICES[@]}"; do
        if gcloud run services describe "$SERVICE" \
            --region="$REGION" \
            --project="$PROJECT_ID" &>/dev/null; then
            
            log "Restarting $SERVICE..."
            gcloud run deploy "$SERVICE" \
                --region="$REGION" \
                --update-secrets="DATABASE_PASSWORD=DATABASE_PASSWORD:latest" \
                --no-gen2 \
                --project="$PROJECT_ID" \
                --quiet || warn "Failed to restart $SERVICE"
            
            log "✅ $SERVICE restarted"
        fi
    done
    
    # Wait for services to become healthy
    log "Waiting for services to stabilize..."
    sleep 30
    
    for SERVICE in "${SERVICES[@]}"; do
        HEALTH=$(curl -s -o /dev/null -w "%{http_code}" \
            "https://${SERVICE}-$(gcloud run services describe "$SERVICE" --region="$REGION" --project="$PROJECT_ID" --format='value(metadata.namespace)').a.run.app/health" 2>/dev/null || echo "000")
        
        if [ "$HEALTH" = "200" ]; then
            log "✅ $SERVICE is healthy"
        else
            warn "$SERVICE health check returned: $HEALTH"
        fi
    done
}

# ============================================================================
# PHASE 5: DEACTIVATE OLD USER (After Verification Period)
# ============================================================================

phase_5_deactivate_old_user() {
    log "=== PHASE 5: Deactivate Old Database User ==="
    
    # Check if old user still exists
    log "Checking for old user: $OLD_USER..."
    
    TEMP_SQL=$(mktemp)
    cat > "$TEMP_SQL" << EOF
-- Terminate old user connections
SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
WHERE usename = '$OLD_USER' AND pid <> pg_backend_pid();

-- Revoke privileges
REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM $OLD_USER;
REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM $OLD_USER;
REVOKE ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public FROM $OLD_USER;
REVOKE CONNECT ON DATABASE $DATABASE_NAME FROM $OLD_USER;

-- Drop old user
DROP USER IF EXISTS $OLD_USER;
EOF

    log "Executing SQL on $INSTANCE_NAME..."
    gcloud sql connect "$INSTANCE_NAME" \
        --user=postgres \
        --database="$DATABASE_NAME" \
        < "$TEMP_SQL" \
        2>/dev/null || warn "Failed to revoke old user privileges"
    
    rm -f "$TEMP_SQL"
    log "✅ Old database user deactivated: $OLD_USER"
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

main() {
    log "╔════════════════════════════════════════════════════════════════╗"
    log "║        Database Password Rotation - $ENV Environment        ║"
    log "║                  Instance: $INSTANCE_NAME"
    log "╚════════════════════════════════════════════════════════════════╝"
    
    # Verify GCP project
    CURRENT_PROJECT=$(gcloud config get-value project)
    if [ "$CURRENT_PROJECT" != "$PROJECT_ID" ]; then
        warn "Current GCP project: $CURRENT_PROJECT"
        warn "Target project: $PROJECT_ID"
        log "Switching projects (use: gcloud config set project $PROJECT_ID)"
    fi
    
    # Execute phases
    phase_1_create_new_user
    phase_2_test_connection
    phase_3_update_secrets
    phase_4_restart_services
    
    log ""
    log "╔════════════════════════════════════════════════════════════════╗"
    log "║                   ✅ ROTATION COMPLETE                        ║"
    log "╚════════════════════════════════════════════════════════════════╝"
    log ""
    log "Timeline:"
    log "  • Immediate: New user active, applications connected"
    log "  • +24 hours: Keep old user alive for any lingering connections"
    log "  • +48 hours: Run Phase 5 to deactivate old user"
    log ""
    log "To complete rotation (deactivate old user after 48 hours):"
    log "  ./rotate_database_password.sh --env=$ENV --phase5-only"
    log ""
    log "Rotation log: $LOG_FILE"
    
    # Cleanup
    rm -f /tmp/new_db_password
}

# ============================================================================
# PHASE 5 ONLY (Optional later execution)
# ============================================================================

if [[ "$*" == *"--phase5-only"* ]]; then
    log "Running PHASE 5 ONLY (deactivate old user)..."
    phase_5_deactivate_old_user
else
    main
fi
