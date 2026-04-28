# Namespace-isolated Kubernetes Service

## Overview
This project deploys a web API into a dedicated namespace and adds ingress routing and horizontal autoscaling.

## Why This Project Matters
It shows how teams separate workloads, expose selected paths safely, and scale based on platform metrics.

## Architecture Explanation
- A namespace provides basic tenancy boundaries.
- A Deployment and Service run the application internally.
- An Ingress publishes HTTP traffic.
- An HPA adjusts replica counts based on load.

## Setup Instructions
1. Install `kubectl` and confirm cluster access.
2. Install an ingress controller and metrics server if they are not already present.
3. Apply the manifests with `kubectl apply -f .`.
4. Add the ingress host to local DNS or a real DNS record.

## Deployment Steps
1. Push the image tag referenced by the Deployment.
2. Apply the namespace and workload manifests.
3. Confirm rollout health and ingress reachability.
4. Generate load and verify HPA behavior.

## Security Best Practices
- Use a dedicated namespace and label resources consistently.
- Avoid NodePort unless specifically required.
- Limit exposed ingress paths.
- Keep secrets out of ConfigMaps.

