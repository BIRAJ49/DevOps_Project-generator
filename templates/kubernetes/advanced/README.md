# Blue-Green Kubernetes Rollout

## Overview
This project demonstrates a blue-green Kubernetes deployment strategy with ingress, autoscaling, and network isolation controls.

## Why This Project Matters
It provides a safer release model for production services where rollback speed and traffic control matter.

## Architecture Explanation
- Blue and green Deployments run side by side.
- A stable Service points to one color at a time.
- Ingress exposes the public route.
- HPA and NetworkPolicy add resilience and control.

## Setup Instructions
1. Install `kubectl`, an ingress controller, and the metrics server.
2. Apply all manifests.
3. Confirm the blue deployment is healthy.
4. Shift the Service selector to the green deployment during rollout.

## Deployment Steps
1. Build and publish the candidate image.
2. Update the green deployment image tag.
3. Validate readiness and internal smoke tests.
4. Switch live traffic by patching the Service selector.
5. Roll back by returning the selector to blue if needed.

## Security Best Practices
- Keep external access limited to ingress-managed routes.
- Use NetworkPolicy to constrain lateral movement.
- Avoid embedding credentials in manifests.
- Scope service accounts and RBAC to the minimum required privileges.

