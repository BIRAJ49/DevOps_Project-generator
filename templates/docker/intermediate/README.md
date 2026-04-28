# Multi-stage FastAPI Service Behind Nginx

## Overview
This project shows how to package a Python API with a multi-stage Docker build and expose it through an Nginx reverse proxy.

## Why This Project Matters
It introduces production-oriented image layering, clearer separation between app and edge traffic, and health checks across multiple containers.

## Architecture Explanation
- The FastAPI service listens on an internal port inside the Compose network.
- Nginx forwards external HTTP traffic to the API container.
- Compose health checks confirm both the application and proxy are responding.

## Setup Instructions
1. Install Docker and Docker Compose.
2. Run `docker compose build`.
3. Run `docker compose up`.
4. Open `http://localhost:8080/health`.

## Deployment Steps
1. Build and tag the API image.
2. Publish the image to a registry.
3. Apply the Nginx configuration in the target environment.
4. Route production traffic through the proxy and monitor health.

## Security Best Practices
- Keep the runtime image separate from the build layer.
- Restrict exposed ports to the proxy entry point.
- Store secrets outside the image.
- Add HTTPS termination before exposing the proxy publicly.

