# Reusable GitHub Actions Pipeline with OIDC

## Overview
This project uses a reusable build workflow and environment-specific deployment jobs that authenticate to cloud infrastructure through GitHub OIDC.

## Why This Project Matters
It reduces workflow duplication, removes long-lived cloud keys from GitHub Secrets, and makes promotion controls more explicit.

## Architecture Explanation
- A reusable workflow handles tests, image builds, and registry publication.
- A top-level workflow calls the reusable workflow and then deploys by environment.
- Cloud access is granted through short-lived OIDC sessions instead of static credentials.

## Setup Instructions
1. Create cloud IAM roles that trust GitHub OIDC.
2. Set repository variables such as `REGISTRY`, `STAGING_ROLE_ARN`, and `PRODUCTION_ROLE_ARN`.
3. Store only non-OIDC secrets such as notifications or app-specific tokens in GitHub Secrets.
4. Enable protected environments for staging and production.

## Deployment Steps
1. Run the reusable build workflow on pull requests and `main`.
2. Publish the image digest from the build job.
3. Deploy to staging automatically after a successful main branch build.
4. Require human approval before production deployment.

## Security Best Practices
- Use least-privilege OIDC roles for each environment.
- Keep workflow permissions minimal and explicit.
- Pin actions to stable releases.
- Restrict production deployment to protected branches and approved environments.

