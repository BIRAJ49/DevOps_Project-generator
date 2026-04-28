# Terraform Artifact Bucket

## Overview
This project provisions a private S3 bucket for CI artifacts with versioning and encryption enabled.

## Why This Project Matters
It provides a safe first Terraform project with immediate operational value and a small blast radius.

## Architecture Explanation
- Terraform manages one private S3 bucket.
- Bucket versioning protects against accidental overwrites.
- Server-side encryption and public access blocks enforce a safer baseline.

## Setup Instructions
1. Install Terraform and authenticate to AWS through your preferred secure mechanism.
2. Copy the variables into a `terraform.tfvars` file or pass them at apply time.
3. Run `terraform init`.
4. Run `terraform plan` and `terraform apply`.

## Deployment Steps
1. Validate the plan output.
2. Apply the configuration in the target account.
3. Export the bucket outputs into your CI system.
4. Review retention and lifecycle settings over time.

## Security Best Practices
- Use short-lived AWS credentials or workload identity.
- Keep the bucket private and encrypted.
- Restrict upload permissions to the CI role only.
- Store Terraform state securely in a remote backend for team use.

