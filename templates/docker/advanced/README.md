# Event-driven Deployment Tracker

## Overview
This template packages an API, background worker, and Redis queue into a multi-container Docker Compose stack.

## Why This Project Matters
It demonstrates how to structure asynchronous platform workflows with separate service responsibilities and minimal external exposure.

## Architecture Explanation
- A FastAPI API receives deployment events.
- Redis stores queued jobs for asynchronous processing.
- A worker container consumes deployment jobs and writes result logs.

## Setup Instructions
1. Install Docker and Docker Compose.
2. Run `docker compose build`.
3. Run `docker compose up`.
4. POST a deployment event to `http://localhost:8000/deployments`.

## Deployment Steps
1. Build and scan both service images.
2. Push images to a private registry.
3. Replace Redis with a managed queue if higher durability is required.
4. Add metrics, alerts, and retry policies before production rollout.

## Security Best Practices
- Expose only the API port publicly.
- Keep Redis on an internal-only network.
- Use secrets or vault-managed tokens for real deployment credentials.
- Enforce least-privilege runtime permissions for both containers.

