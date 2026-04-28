# Staged CI/CD Pipeline with Security Scan

## Overview
This project adds artifact publishing, image scanning, and a staged Kubernetes deployment step to a GitHub Actions pipeline.

## Why This Project Matters
It teaches teams how to move from simple CI into controlled delivery without skipping security and approval gates.

## Architecture Explanation
- Pull requests trigger lint, test, and image build validation.
- The main branch also publishes a container image.
- A deployment job applies Kubernetes manifests to staging after the artifact is scanned.

## Setup Instructions
1. Create a GitHub repository and enable Actions.
2. Add `REGISTRY_USERNAME`, `REGISTRY_PASSWORD`, and `KUBECONFIG_BASE64` secrets.
3. Replace the placeholder image and namespace values.
4. Push to `main` and review the workflow run.

## Deployment Steps
1. Build, tag, and scan the image.
2. Push the image to a private registry.
3. Apply the staging manifest with `kubectl`.
4. Add a production environment for the next promotion stage.

## Security Best Practices
- Use GitHub Secrets or OIDC instead of plaintext credentials.
- Fail builds on critical scan findings.
- Limit deploy permissions to trusted branches and environments.
- Keep kubeconfig scoped to the target namespace only.

