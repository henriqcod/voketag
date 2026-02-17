terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  # LOW FIX: Enable state locking with Cloud Storage backend
  # Prevents concurrent terraform applies
  # To use: terraform init -backend-config="bucket=YOUR_BUCKET_NAME"
  backend "gcs" {
    prefix = "terraform/state"
    # bucket must be specified via -backend-config or environment variable
    # Enable versioning on the bucket for state history
  }
}

variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

provider "google" {
  project = var.project_id
  region  = var.region
}
