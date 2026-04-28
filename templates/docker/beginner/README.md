# Containerized FastAPI Health and Release Notes Service

## Overview
This project packages a lightweight FastAPI service into a Docker image and runs it with Docker Compose.

## Why This Project Matters
It introduces repeatable container builds, port management, health checks, and local orchestration with a small deployment surface.

## Architecture Explanation
- One FastAPI application container serves HTTP traffic.
- Docker Compose manages the runtime environment and port mapping.
- A dedicated health endpoint supports readiness checks and troubleshooting.

## Setup Instructions
1. Install Docker Desktop or Docker Engine with Compose support.
2. Run `docker compose build`.
3. Run `docker compose up`.
4. Open `http://localhost:8000/health`.

## Deployment Steps
1. Build the production image.
2. Push the image to a private registry.
3. Update deployment targets with the immutable image tag.
4. Attach container health checks in the runtime platform.

## Security Best Practices
- Keep the image base small and patch it regularly.
- Pin Python dependencies.
- Pass secrets through environment variables or a secret manager.
- Expose only the required application port.

