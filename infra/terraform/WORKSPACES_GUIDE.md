# Terraform Workspaces Guide

## 📚 Overview

This guide explains how to use Terraform workspaces to manage multiple environments (dev, staging, production) with the same infrastructure code.

**LOW ENHANCEMENT:** Better environment organization and isolation.

---

## 🎯 Why Workspaces?

### Benefits:
- ✅ **Environment isolation** - Separate state for each environment
- ✅ **DRY principle** - Same code for all environments
- ✅ **Easy switching** - Change between environments quickly
- ✅ **Safety** - Prevents accidental changes to wrong environment

### When to Use:
- Multiple environments (dev/staging/prod)
- Same infrastructure with different configurations
- Team collaboration (each dev has own workspace)

---

## 🚀 Quick Start

### 1. Initialize Terraform

```bash
cd infra/terraform
terraform init
```

### 2. Create Workspaces

```bash
# Create development workspace
terraform workspace new dev

# Create staging workspace
terraform workspace new staging

# Create production workspace
terraform workspace new production
```

### 3. List Workspaces

```bash
terraform workspace list

# Output:
# * default
#   dev
#   staging
#   production
```

### 4. Switch Between Workspaces

```bash
# Switch to development
terraform workspace select dev

# Switch to staging
terraform workspace select staging

# Switch to production
terraform workspace select production
```

### 5. Show Current Workspace

```bash
terraform workspace show
# Output: production
```

---

## 📋 Workspace Usage

### Development

```bash
# Switch to dev
terraform workspace select dev

# Plan changes
terraform plan \
  -var-file="environments/dev.tfvars" \
  -var="project_id=voketag-dev"

# Apply changes
terraform apply \
  -var-file="environments/dev.tfvars" \
  -var="project_id=voketag-dev"
```

### Staging

```bash
# Switch to staging
terraform workspace select staging

# Plan and apply
terraform plan -var-file="environments/staging.tfvars"
terraform apply -var-file="environments/staging.tfvars"
```

### Production

```bash
# Switch to production
terraform workspace select production

# Plan and apply (with approval required)
terraform plan -var-file="environments/production.tfvars"
terraform apply -var-file="environments/production.tfvars"
```

---

## 🔧 Configuration per Environment

### Option 1: Use Workspace Name in Code

```hcl
# main.tf
locals {
  env = terraform.workspace
  
  # Environment-specific configuration
  instance_count = {
    dev        = 1
    staging    = 2
    production = 5
  }
  
  min_instances = {
    dev        = 0
    staging    = 1
    production = 2
  }
}

resource "google_cloud_run_v2_service" "scan_service" {
  name     = "scan-service-${local.env}"
  location = var.region

  template {
    min_instance_count = local.min_instances[local.env]
    max_instance_count = local.instance_count[local.env]
    # ...
  }
}
```

### Option 2: Use tfvars Files

Create separate `.tfvars` files for each environment:

**environments/dev.tfvars:**
```hcl
project_id      = "voketag-dev"
region          = "us-central1"
env             = "development"
min_instances   = 0
max_instances   = 2
sre_email       = "dev@voketag.com.br"
```

**environments/staging.tfvars:**
```hcl
project_id      = "voketag-staging"
region          = "us-central1"
env             = "staging"
min_instances   = 1
max_instances   = 5
sre_email       = "staging@voketag.com.br"
```

**environments/production.tfvars:**
```hcl
project_id      = "voketag-prod"
region          = "us-central1"
env             = "production"
min_instances   = 2
max_instances   = 100
sre_email       = "sre@voketag.com.br"
```

---

## 🗂️ Workspace State Storage

Each workspace has its own state file in GCS:

```
gs://voketag-terraform-state/
├── terraform/state/default/default.tfstate
├── terraform/state/dev/default.tfstate
├── terraform/state/staging/default.tfstate
└── terraform/state/production/default.tfstate
```

**State isolation** ensures changes in dev don't affect production.

---

## ⚠️ Best Practices

### 1. Always Verify Current Workspace

```bash
# Before any terraform command, check workspace
terraform workspace show

# Or add to prompt
export PS1='[$(terraform workspace show)] \w\$ '
```

### 2. Use Workspace-Specific Naming

```hcl
# Include workspace in resource names
resource "google_cloud_run_v2_service" "scan_service" {
  name = "scan-service-${terraform.workspace}"
  # ...
}
```

### 3. Require Manual Confirmation for Production

```bash
# Always run plan first in production
terraform workspace select production
terraform plan -var-file="environments/production.tfvars" -out=prod.tfplan

# Review carefully, then apply
terraform apply prod.tfplan
```

### 4. Never Use Default Workspace

```bash
# Create dedicated workspaces, don't use 'default'
terraform workspace new production
terraform workspace select production
```

### 5. Document Workspace Usage

Add to README:

```markdown
## Terraform Workspaces

- `dev` - Development environment
- `staging` - Staging environment  
- `production` - Production environment

Always verify current workspace before running terraform commands:
\`\`\`bash
terraform workspace show
\`\`\`
```

---

## 🔐 CI/CD Integration

### GitHub Actions

```yaml
- name: Select Terraform Workspace
  run: |
    cd infra/terraform
    terraform workspace select ${{ github.event.inputs.environment }}

- name: Terraform Plan
  run: |
    terraform plan \
      -var-file="environments/${{ github.event.inputs.environment }}.tfvars" \
      -out=tfplan

- name: Terraform Apply
  run: terraform apply tfplan
```

---

## 🛠️ Common Commands

```bash
# Create new workspace
terraform workspace new <name>

# List all workspaces
terraform workspace list

# Show current workspace
terraform workspace show

# Switch workspace
terraform workspace select <name>

# Delete workspace (be careful!)
terraform workspace delete <name>
```

---

## 🚨 Troubleshooting

### "Workspace already exists"

```bash
# If workspace exists, just select it
terraform workspace select dev
```

### "Cannot delete current workspace"

```bash
# Switch to another workspace first
terraform workspace select default
terraform workspace delete dev
```

### "State lock"

```bash
# If state is locked, force unlock (careful!)
terraform force-unlock <LOCK_ID>
```

---

## 📊 Comparison: Workspaces vs Separate Directories

| Aspect | Workspaces | Separate Dirs |
|--------|-----------|---------------|
| Code duplication | ❌ None | ✅ Some |
| State isolation | ✅ Yes | ✅ Yes |
| Easy switching | ✅ Yes | ❌ No (cd required) |
| Config per env | ⚠️ Via tfvars | ✅ Via files |
| Learning curve | 🟢 Low | 🟢 Low |
| **Recommended for** | Similar envs | Different infra |

**VokeTag:** Workspaces são ideais porque dev/staging/prod têm infraestrutura similar.

---

## ✅ Setup Checklist

- [x] Terraform initialized (`terraform init`)
- [ ] Workspaces created (dev, staging, production)
- [ ] tfvars files created for each environment
- [ ] Team trained on workspace commands
- [ ] CI/CD updated to use workspaces
- [ ] Documentation updated

---

## 🎯 Next Steps

1. Create workspaces: `terraform workspace new dev/staging/production`
2. Create tfvars files: `environments/dev.tfvars`, etc.
3. Test in dev first: `terraform workspace select dev && terraform plan`
4. Deploy to staging: `terraform workspace select staging && terraform apply`
5. Deploy to production: `terraform workspace select production && terraform apply`

---

**Created:** 2026-02-17  
**Version:** 1.0  
**Enhancement:** LOW (Better organization)
