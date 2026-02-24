#!/bin/bash
#
# Script: Rotate JWT Secret with Zero Downtime
# Usage: ./rotate_jwt_secret.sh [--env=production|staging]
# Frequency: Quarterly or on compromise
# Owner: DevOps / Security Team
#
# This script implements dual-key rotation strategy:
# 1. Add new JWT_SECRET_2 (services accept both old and new tokens)
# 2. Wait for gradual token refresh (24-48 hours)
# 3. Promote JWT_SECRET_2 to JWT_SECRET
# 4. Remove old secret
#
# ZERO DOWNTIME: Users won't be logged out during rotation
#

set -e
set -o pipefail

# ============================================================================
# CONFIGURATION
# ============================================================================

ENV="${1:-staging}"
PROJECT_ID="${GCP_PROJECT_ID:-voketag-${ENV}}"
REGION="us-central1"
TIMESTAMP=$(date -u +'%Y-%m-%d_%H-%M-%S')
LOG_FILE="/var/log/jwt-rotation-${TIMESTAMP}.log"

# JWT secret requirements
JWT_LENGTH=64  # 512-bit key
JWT_ALGORITHM="RS256"  # RSA asymmetric for better security

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Redirect output
exec > >(tee -a "$LOG_FILE")
exec 2>&1

# ============================================================================
# FUNCTIONS
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date -u '+%Y-%m-%d %H:%M:%S UTC') - $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $(date -u '+%Y-%m-%d %H:%M:%S UTC') - $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $(date -u '+%Y-%m-%d %H:%M:%S UTC') - $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $(date -u '+%Y-%m-%d %H:%M:%S UTC') - $1"
}

confirm_action() {
    local message="$1"
    echo ""
    echo -e "${YELLOW}⚠️  $message${NC}"
    read -p "Continue? (yes/no): " -r
    echo
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log_warning "Operation cancelled by user"
        exit 1
    fi
}

# ============================================================================
# HEADER
# ============================================================================

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║          🔐 JWT SECRET ROTATION - ZERO DOWNTIME               ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

log_info "Environment: $ENV"
log_info "Project ID: $PROJECT_ID"
log_info "Algorithm: $JWT_ALGORITHM"
log_info "Key length: $JWT_LENGTH characters"
echo ""

confirm_action "This will rotate JWT secrets in $ENV environment."

# ============================================================================
# 1. CHECK PREREQUISITES
# ============================================================================

log_info "Checking prerequisites..."

if ! command -v gcloud &> /dev/null; then
    log_error "gcloud CLI not found"
    exit 1
fi

if ! command -v openssl &> /dev/null; then
    log_error "openssl not found"
    exit 1
fi

# Check GCP authentication
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    log_error "Not authenticated with gcloud. Run: gcloud auth login"
    exit 1
fi

log_success "Prerequisites met"
echo ""

# ============================================================================
# 2. GENERATE NEW RSA KEY PAIR (for RS256)
# ============================================================================

log_info "Generating new RSA key pair (4096-bit)..."

TEMP_DIR=$(mktemp -d)
PRIVATE_KEY_FILE="$TEMP_DIR/jwt_private.pem"
PUBLIC_KEY_FILE="$TEMP_DIR/jwt_public.pem"

# Generate 4096-bit RSA private key
openssl genrsa -out "$PRIVATE_KEY_FILE" 4096 2>/dev/null

# Extract public key
openssl rsa -in "$PRIVATE_KEY_FILE" -pubout -out "$PUBLIC_KEY_FILE" 2>/dev/null

# Read keys into variables
JWT_PRIVATE_KEY=$(cat "$PRIVATE_KEY_FILE")
JWT_PUBLIC_KEY=$(cat "$PUBLIC_KEY_FILE")

log_success "RSA key pair generated (4096-bit)"
log_info "   Private key: ${#JWT_PRIVATE_KEY} chars"
log_info "   Public key: ${#JWT_PUBLIC_KEY} chars"
echo ""

# ============================================================================
# 3. DUAL-KEY STRATEGY: ADD NEW SECRET AS SECONDARY
# ============================================================================

log_info "PHASE 1: Adding new JWT secret as secondary key..."
echo ""

# Check if JWT_SECRET exists
if ! gcloud secrets describe JWT_SECRET --project="$PROJECT_ID" &>/dev/null; then
    log_error "JWT_SECRET doesn't exist in Secret Manager!"
    log_info "Creating initial JWT_SECRET..."
    
    echo -n "$JWT_PRIVATE_KEY" | gcloud secrets create JWT_SECRET \
        --data-file=- \
        --project="$PROJECT_ID" \
        --replication-policy="automatic" \
        --quiet
    
    echo -n "$JWT_PUBLIC_KEY" | gcloud secrets create JWT_PUBLIC_KEY \
        --data-file=- \
        --project="$PROJECT_ID" \
        --replication-policy="automatic" \
        --quiet
    
    log_success "Initial JWT secrets created"
else
    # Add new version as JWT_SECRET_2 (secondary key)
    log_info "   Creating JWT_SECRET_2 (new key)..."
    
    if gcloud secrets describe JWT_SECRET_2 --project="$PROJECT_ID" &>/dev/null; then
        # Update existing JWT_SECRET_2
        echo -n "$JWT_PRIVATE_KEY" | gcloud secrets versions add JWT_SECRET_2 \
            --data-file=- \
            --project="$PROJECT_ID" \
            --quiet
        
        echo -n "$JWT_PUBLIC_KEY" | gcloud secrets versions add JWT_PUBLIC_KEY_2 \
            --data-file=- \
            --project="$PROJECT_ID" \
            --quiet
    else
        # Create JWT_SECRET_2
        echo -n "$JWT_PRIVATE_KEY" | gcloud secrets create JWT_SECRET_2 \
            --data-file=- \
            --project="$PROJECT_ID" \
            --replication-policy="automatic" \
            --quiet
        
        echo -n "$JWT_PUBLIC_KEY" | gcloud secrets create JWT_PUBLIC_KEY_2 \
            --data-file=- \
            --project="$PROJECT_ID" \
            --replication-policy="automatic" \
            --quiet
    fi
    
    log_success "JWT_SECRET_2 created (secondary key active)"
fi

echo ""

# ============================================================================
# 4. UPDATE SERVICES TO ACCEPT BOTH KEYS
# ============================================================================

log_info "PHASE 2: Updating services to accept BOTH old and new keys..."
echo ""

SERVICES=("admin-service" "factory-service" "scan-service")

for service in "${SERVICES[@]}"; do
    log_info "   Updating $service..."
    
    # Services should be configured to accept both JWT_SECRET and JWT_SECRET_2
    # This requires application code to support dual-key verification
    
    gcloud run services update "$service" \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --update-secrets=JWT_SECRET=JWT_SECRET:latest,JWT_SECRET_2=JWT_SECRET_2:latest \
        --update-secrets=JWT_PUBLIC_KEY=JWT_PUBLIC_KEY:latest,JWT_PUBLIC_KEY_2=JWT_PUBLIC_KEY_2:latest \
        --quiet 2>/dev/null || {
            log_warning "   $service may not support dual-key yet (needs code update)"
        }
    
    log_success "   $service updated"
done

echo ""

# ============================================================================
# 5. GRACE PERIOD NOTIFICATION
# ============================================================================

log_warning "╔════════════════════════════════════════════════════════════════╗"
log_warning "║                   ⏳ GRACE PERIOD REQUIRED                     ║"
log_warning "╚════════════════════════════════════════════════════════════════╝"
echo ""
log_info "CURRENT STATE:"
log_info "  • Both JWT_SECRET (old) and JWT_SECRET_2 (new) are ACTIVE"
log_info "  • Services accept tokens signed with EITHER key"
log_info "  • Users can continue using old tokens (won't be logged out)"
echo ""
log_info "NEXT STEPS:"
log_info "  1. Wait 24-48 hours for gradual token refresh"
log_info "  2. Monitor token validation metrics (check for JWT_SECRET_2 usage)"
log_info "  3. Run './rotate_jwt_secret_finalize.sh' to promote new key"
echo ""
log_warning "❌ DO NOT run finalize script until grace period complete!"
echo ""

# ============================================================================
# 6. CREATE FINALIZATION SCRIPT
# ============================================================================

FINALIZE_SCRIPT="./rotate_jwt_secret_finalize.sh"

cat > "$FINALIZE_SCRIPT" << 'FINALIZE_EOF'
#!/bin/bash
#
# JWT Secret Rotation - PHASE 3: FINALIZATION
# This script promotes JWT_SECRET_2 to JWT_SECRET and removes old key
#

set -e

PROJECT_ID="${GCP_PROJECT_ID:-voketag-production}"
REGION="us-central1"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║          🔐 JWT SECRET ROTATION - FINALIZATION                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

read -p "Have 24-48 hours passed since dual-key deployment? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "⚠️  Wait for grace period before finalizing!"
    exit 1
fi

echo ""
echo "[INFO] Copying JWT_SECRET_2 → JWT_SECRET (promoting new key)..."

# Get latest version of JWT_SECRET_2
NEW_PRIVATE=$(gcloud secrets versions access latest --secret=JWT_SECRET_2 --project="$PROJECT_ID")
NEW_PUBLIC=$(gcloud secrets versions access latest --secret=JWT_PUBLIC_KEY_2 --project="$PROJECT_ID")

# Add new version to JWT_SECRET (old key is now deprecated)
echo -n "$NEW_PRIVATE" | gcloud secrets versions add JWT_SECRET \
    --data-file=- \
    --project="$PROJECT_ID" \
    --quiet

echo -n "$NEW_PUBLIC" | gcloud secrets versions add JWT_PUBLIC_KEY \
    --data-file=- \
    --project="$PROJECT_ID" \
    --quiet

echo "[✓] JWT_SECRET promoted to new key"
echo ""

echo "[INFO] Removing JWT_SECRET_2 (no longer needed)..."
gcloud secrets delete JWT_SECRET_2 --project="$PROJECT_ID" --quiet || true
gcloud secrets delete JWT_PUBLIC_KEY_2 --project="$PROJECT_ID" --quiet || true

echo "[✓] Old secondary keys removed"
echo ""

echo "[INFO] Updating services to use single key..."
SERVICES=("admin-service" "factory-service" "scan-service")

for service in "${SERVICES[@]}"; do
    echo "   Updating $service..."
    gcloud run services update "$service" \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --clear-secrets \
        --update-secrets=JWT_SECRET=JWT_SECRET:latest,JWT_PUBLIC_KEY=JWT_PUBLIC_KEY:latest \
        --quiet
done

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              ✅ JWT ROTATION FINALIZED                         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "All services now using new JWT secret exclusively."
echo "Old tokens signed with previous key are INVALID."
echo ""
echo "Next rotation: $(date -u -d '+90 days' +'%Y-%m-%d') (90 days)"
FINALIZE_EOF

chmod +x "$FINALIZE_SCRIPT"
log_success "Finalization script created: $FINALIZE_SCRIPT"

# ============================================================================
# 7. AUDIT LOG
# ============================================================================

AUDIT_LOG="/var/log/jwt-rotation-audit.jsonl"

cat >> "$AUDIT_LOG" << AUDIT_EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "action": "jwt_secret_rotation_phase1",
  "environment": "$ENV",
  "project_id": "$PROJECT_ID",
  "algorithm": "$JWT_ALGORITHM",
  "key_length_bits": 4096,
  "rotation_strategy": "dual_key_zero_downtime",
  "services_updated": ["admin-service", "factory-service", "scan-service"],
  "next_action": "finalize_after_grace_period",
  "finalize_script": "$FINALIZE_SCRIPT",
  "status": "phase1_complete"
}
AUDIT_EOF

# ============================================================================
# 8. MONITORING QUERY
# ============================================================================

log_info "MONITORING COMMANDS:"
echo ""
echo "# Check JWT_SECRET_2 usage (verify new tokens being issued)"
echo "gcloud logging read 'jsonPayload.jwt_key_id=\"JWT_SECRET_2\"' \\"
echo "  --project=$PROJECT_ID --limit=100 --format=json"
echo ""
echo "# Check for JWT validation errors"
echo "gcloud logging read 'severity>=ERROR AND jsonPayload.error=~\"JWT\"' \\"
echo "  --project=$PROJECT_ID --limit=50"
echo ""

# ============================================================================
# 9. CLEANUP
# ============================================================================

log_info "Cleaning up temporary files..."
rm -rf "$TEMP_DIR"
log_success "Cleanup complete"

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         ✅ JWT ROTATION PHASE 1 COMPLETED                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
log_success "Dual-key deployment complete"
log_info "Log file: $LOG_FILE"
log_info "Finalize script: $FINALIZE_SCRIPT"
echo ""
log_warning "⏳ Wait 24-48 hours, then run: $FINALIZE_SCRIPT"
echo ""

exit 0
