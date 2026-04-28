# Kubernetes Release Catalog API

## Overview
This project deploys a small API into Kubernetes with a Deployment, a ClusterIP Service, and a ConfigMap.

## Why This Project Matters
It provides a practical baseline for understanding how Kubernetes schedules workloads and routes traffic safely.

## Architecture Explanation
- A Deployment maintains multiple API pod replicas.
- A ConfigMap provides non-secret runtime configuration.
- A ClusterIP Service exposes the pods internally.

## Setup Instructions
1. Install `kubectl` and point it at a cluster.
2. Apply the manifests with `kubectl apply -f .`.
3. Check rollout status with `kubectl rollout status deployment/release-catalog`.
4. Port-forward the service to test it locally.

## Deployment Steps
1. Build and push the application image.
2. Update the image tag in the Deployment manifest.
3. Apply the manifests to the cluster.
4. Monitor pod health and readiness.

## Security Best Practices
- Use ClusterIP unless public exposure is required.
- Store secrets in a secret manager or Kubernetes Secret objects.
- Set explicit resource requests and limits.
- Run containers as non-root where possible.

