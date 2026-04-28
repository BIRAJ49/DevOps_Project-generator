#!/usr/bin/env bash
set -euo pipefail

ENVIRONMENT="${1:-staging}"
IMAGE_DIGEST="${2:-ghcr.io/example/release-gateway@sha256:replace-me}"

echo "Deploying ${IMAGE_DIGEST} to ${ENVIRONMENT}"
kubectl -n "${ENVIRONMENT}" set image deployment/release-gateway release-gateway="${IMAGE_DIGEST}"

