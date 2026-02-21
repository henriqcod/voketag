# Terraform backend configuration with state locking
# Prevents concurrent terraform applies that could cause state corruption
#
# To initialize with this backend:
# 1. Create a GCS bucket (or use existing):
#    gsutil mb gs://your-project-terraform-state
#
# 2. Enable versioning on the bucket for state history:
#    gsutil versioning set on gs://your-project-terraform-state
#
# 3. Initialize terraform with backend config:
#    terraform init -backend-config="bucket=your-project-terraform-state" \
#                   -backend-config="prefix=production"
#
# 4. Verify state locking is working:
#    terraform refresh -lock
#
# State locking with GCS:
# - Terraform uses a lock file (terraform.lock) in the bucket
# - Lock is automatically acquired during terraform operations
# - Lock timeout can be configured (default 10s for GCS)
# - Works across multiple machines for team collaboration

terraform {
  # GCS backend with state locking enabled
  backend "gcs" {
    # Bucket name (specify via -backend-config or TF_VAR_backend_bucket env var)
    # bucket = "your-project-terraform-state"

    # State file prefix for environment isolation
    prefix = "terraform/state"

    # Enable versioning on bucket for state history:
    # gsutil versioning set on gs://your-bucket

    # State locking is automatically enabled with GCS backend
    # Terraform creates a lock file for distributed locking

    # Advanced options (for team workflows):
    # - skip_bucket_versioning: false (keep enabled for disaster recovery)
    # - encryption_key: "" (use for customer-managed encryption)
  }
}
