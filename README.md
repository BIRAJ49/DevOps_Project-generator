# ProjectOps

ProjectOps is a full-stack project idea planner and DevOps deployment demo. It has two parts:

- **Part 1: ProjectOps application** - a React and FastAPI web app that suggests software project ideas and expands selected ideas into implementation plans.
- **Part 2: DevOps implementation** - a hybrid deployment that uses AWS EC2 for the public production demo and local Kubernetes for GitOps, scaling, ingress, network policy, and self-healing demonstrations.

## Live Demo

- Public app: [https://projectops.birajadhikari49.com.np](https://projectops.birajadhikari49.com.np)
- Local Kubernetes demo: `http://autohealops.local:8081`

![ProjectOps public homepage](docs/screenshots/01-ec2-homepage.png)

---

# Part 1: ProjectOps Application

## What The App Does

ProjectOps helps users turn a rough project idea into a structured implementation plan.

- Suggests project ideas from a topic or stack.
- Expands a selected idea into architecture, tools, implementation steps, deliverables, and risks.
- Supports guest usage limits and authenticated usage.
- Uses email verification for signup and password reset.
- Stores users, usage records, and generated artifact metadata in PostgreSQL.
- Includes starter template content for Docker, Kubernetes, CI/CD, and Terraform projects.

![Generated project options](docs/screenshots/02-ec2-generate-result.png)

## Application Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | React, Vite, React Router, lucide-react |
| Backend | FastAPI, SQLAlchemy, Pydantic |
| Database | PostgreSQL |
| Auth | JWT, bcrypt, email verification |
| Email | Resend API |
| Packaging | Docker, Docker Compose |
| Templates | JSON, YAML, Docker, Terraform, Python, Node.js starter files |

## Project Structure

```text
DevOps_Project_generator/
├── backend/
│   ├── auth/
│   ├── models/
│   ├── routes/
│   ├── services/
│   ├── utils/
│   ├── Dockerfile
│   └── main.py
├── frontend/
│   ├── src/
│   ├── Dockerfile
│   └── nginx.conf
├── k8s/
│   ├── backend-deployment.yaml
│   ├── backend-service.yaml
│   ├── configmap.yaml
│   ├── database-deployment.yaml
│   ├── frontend-deployment.yaml
│   ├── frontend-service.yaml
│   ├── hpa.yaml
│   ├── ingress.yaml
│   ├── namespace.yaml
│   ├── network-policy.yaml
│   ├── secret.example.yaml
│   └── service-account.yaml
├── templates/
├── docs/screenshots/
├── docker-compose.yml
├── docker-compose.prod.yml
└── README.md
```

## API Overview

### Auth

- `POST /api/signup`
- `POST /api/verify-email`
- `POST /api/resend-verification`
- `POST /api/login`
- `GET /api/me`
- `POST /api/forgot-password`
- `POST /api/verify-reset-code`
- `POST /api/reset-password`

### Project Planning

- `POST /api/suggest`
- `POST /api/details`

Example:

```bash
curl -X POST http://127.0.0.1:8000/api/suggest \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"Kubernetes DevOps project"}'
```

## Local App Development

Create an environment file:

```bash
cp .env.example .env
```

Minimum local values:

```env
DATABASE_URL=postgresql+psycopg://autohealops:autohealops@postgres:5432/autohealops
JWT_SECRET_KEY=replace-this-with-at-least-32-characters
FRONTEND_ORIGINS=http://localhost:8080,http://127.0.0.1:8080,http://localhost:5173,http://127.0.0.1:5173
ARTIFACT_STORAGE_BACKEND=local
```

Start the local Docker Compose stack:

```bash
docker compose up -d
```

Open:

```text
http://localhost:8080
```

Run backend tests:

```bash
python -m pip install -r backend/requirements.txt
python -m pytest backend/tests
```

Build frontend:

```bash
cd frontend
npm install
npm run build
```

---

# Part 2: DevOps Implementation

## Final Hybrid Architecture

The final deployment intentionally separates cheap public hosting from heavier Kubernetes DevOps demonstrations.

| Part | Runs On | Reason |
| --- | --- | --- |
| React frontend | AWS EC2 with Docker/Nginx | Public demo, simple hosting |
| FastAPI backend | AWS EC2 with Docker Compose | Realistic small production deployment |
| PostgreSQL | Docker container on EC2 | Avoids RDS cost for demo |
| HTTPS/domain | Caddy on EC2 | Automatic TLS and reverse proxy |
| Kubernetes | Local k3d cluster | Avoids EKS cost |
| Argo CD | Local Kubernetes | GitOps sync and self-heal demo |
| HPA, NetworkPolicy, Ingress | Local Kubernetes | Advanced Kubernetes concepts |
| Prometheus/Grafana/Loki | Deferred | Too heavy for the current free-tier EC2 instance |

## Production Deployment On AWS EC2

The public production app runs on a small EC2 instance using Docker Compose.

![AWS EC2 instance running](docs/screenshots/11-aws-ec2-instance-running.png)

### EC2 Stack

```text
Caddy :80/:443
  -> 127.0.0.1:8080
      -> frontend container, Nginx
          -> /api proxy to backend container
              -> PostgreSQL container
```

### Production Compose

The production stack is defined in `docker-compose.prod.yml`:

- `postgres`
- `backend`
- `frontend`

The frontend binds only to loopback:

```yaml
ports:
  - "127.0.0.1:${FRONTEND_PORT:-8080}:8080"
```

That means port `8080` is not publicly exposed. Caddy is the only public entrypoint.

![Docker Compose running on EC2](docs/screenshots/13-ec2-docker-compose-running.png)

### EC2 Deployment Commands

Install Docker on Ubuntu, clone the repo, create `.env`, then start the production stack:

```bash
git clone https://github.com/biraj49/DevOps_Project-generator.git
cd DevOps_Project-generator

cp .env.example .env
nano .env

docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml ps
```

Example production environment values:

```env
POSTGRES_DB=autohealops
POSTGRES_USER=autohealops
POSTGRES_PASSWORD=replace-with-strong-db-password
DATABASE_URL=postgresql+psycopg://autohealops:replace-with-strong-db-password@postgres:5432/autohealops
JWT_SECRET_KEY=replace-with-a-long-random-secret
FRONTEND_ORIGINS=https://projectops.birajadhikari49.com.np
ARTIFACT_STORAGE_BACKEND=local
EMAIL_FROM=ProjectOps <contact@birajadhikari49.com.np>
RESEND_API_KEY=replace-with-resend-api-key
```

Do not commit real `.env` values.

### HTTPS With Caddy

Caddy terminates HTTPS and proxies to the private frontend port.

`/etc/caddy/Caddyfile`:

```caddy
projectops.birajadhikari49.com.np {
    reverse_proxy 127.0.0.1:8080
}
```

Validate and reload:

```bash
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

### AWS Security Group

Inbound rules:

| Port | Purpose | Source |
| --- | --- | --- |
| 22 | SSH | Your IP only |
| 80 | HTTP redirect / certificate challenge | `0.0.0.0/0` |
| 443 | HTTPS app traffic | `0.0.0.0/0` |

Port `8080` is intentionally not public.

![AWS security group rules](docs/screenshots/12-aws-security-group-rules.png)

### Database Backup

Create a simple PostgreSQL dump:

```bash
mkdir -p ~/backups

docker compose -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U autohealops -d autohealops > ~/backups/autohealops-$(date +%F-%H%M).sql
```

## Local Kubernetes Deployment

The Kubernetes deployment runs locally in k3d so the advanced DevOps features can be demonstrated without EKS cost.

![Local Kubernetes app](docs/screenshots/03-local-k8s-homepage.png)

### Kubernetes Features

The `k8s/` folder includes:

- Namespace
- ConfigMap for non-secret config
- Secret example for sensitive config
- Frontend Deployment and Service
- Backend Deployment and Service
- PostgreSQL database Deployment, Service, and PVC
- Ingress
- Horizontal Pod Autoscaler
- NetworkPolicy
- ServiceAccount
- Readiness and liveness probes
- CPU and memory requests/limits

### Create Local Cluster

```bash
k3d cluster create autohealops \
  --agents 2 \
  -p "8081:80@loadbalancer"
```

Add local DNS:

```bash
sudo sh -c 'grep -q "autohealops.local" /etc/hosts || echo "127.0.0.1 autohealops.local" >> /etc/hosts'
```

### Build And Import Images

```bash
docker build -t autohealops-backend:local -f backend/Dockerfile .
docker build -t autohealops-frontend:local --build-arg VITE_API_BASE_URL= frontend

k3d image import autohealops-backend:local autohealops-frontend:local -c autohealops
```

### Apply Manifests

```bash
kubectl apply -f k8s/
```

Verify:

```bash
kubectl -n autohealops get pods
kubectl -n autohealops get svc
kubectl -n autohealops get ingress
kubectl -n autohealops get hpa
```

![Kubernetes pods running](docs/screenshots/04-k8s-pods-running.png)

![Kubernetes HPA status](docs/screenshots/05-k8s-hpa.png)

![Kubernetes ingress](docs/screenshots/06-k8s-ingress.png)

## GitOps With Argo CD

Argo CD runs in the local Kubernetes cluster and syncs the `k8s/` folder from GitHub.

### Install Argo CD

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

Open the UI:

```bash
kubectl -n argocd port-forward svc/argocd-server 8082:443
```

Get the initial password:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d && echo
```

Open:

```text
https://localhost:8082
```

### Argo CD Application

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: autohealops
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/biraj49/DevOps_Project-generator.git
    targetRevision: main
    path: k8s
  destination:
    server: https://kubernetes.default.svc
    namespace: autohealops
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

Current state:

```text
autohealops   Synced   Healthy
```

![Argo CD synced and healthy](docs/screenshots/07-argocd-synced-healthy.png)

![Argo CD resource tree](docs/screenshots/08-argocd-resource-tree.png)

## Self-Healing Demonstrations

### Kubernetes Pod Self-Healing

Deleting a backend pod causes the Deployment to create a replacement automatically.

```bash
kubectl -n autohealops get pods -l app.kubernetes.io/name=autohealops-backend
kubectl -n autohealops delete pod <backend-pod-name>
kubectl -n autohealops get pods -l app.kubernetes.io/name=autohealops-backend
```

![Kubernetes pod self-healing](docs/screenshots/09-k8s-pod-self-healing.png)

### Argo CD GitOps Self-Healing

Manually scaling the frontend to 1 replica is reverted by Argo CD because Git defines 2 replicas.

```bash
kubectl -n autohealops get deployment autohealops-frontend
kubectl -n autohealops scale deployment autohealops-frontend --replicas=1
kubectl -n autohealops get deployment autohealops-frontend
```

After Argo CD self-heal:

```bash
kubectl -n autohealops get deployment autohealops-frontend
```

![Argo CD GitOps self-healing](docs/screenshots/10-argocd-gitops-self-healing.png)

## Why Not EKS?

This project intentionally avoids EKS to keep the demo free-tier friendly.

- EC2 hosts the public production app with Docker Compose.
- Local k3d demonstrates Kubernetes, Argo CD, HPA, NetworkPolicy, and self-healing.
- Prometheus, Grafana, and Loki are deferred because they are too heavy for the current small EC2 instance.

K3s on EC2 was evaluated, but the current instance has limited memory and disk. Docker Compose is the more reliable production choice for this free-tier style deployment.

## CI/CD

GitHub Actions runs:

- Backend tests
- Docker image builds
- GHCR image publishing on pushes to `main`

Images:

```text
ghcr.io/biraj49/devops_project-generator/backend:latest
ghcr.io/biraj49/devops_project-generator/frontend:latest
```

## Useful Commands

### EC2 Production

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

### Local Kubernetes

```bash
kubectl -n autohealops get pods
kubectl -n autohealops get hpa
kubectl -n autohealops get ingress
kubectl -n argocd get application autohealops
```

### Stop Local k3d

```bash
k3d cluster stop autohealops
```

### Delete Local k3d

```bash
k3d cluster delete autohealops
```

## Security Notes

- `.env` is ignored and must not be committed.
- Rotate any API key that was accidentally shared.
- SSH is restricted to a single IP in the EC2 security group.
- Public traffic uses HTTPS through Caddy.
- Docker Compose exposes the frontend only on `127.0.0.1:8080`.
- Kubernetes uses NetworkPolicy for basic ingress control.
- Kubernetes secrets in `secret.example.yaml` are examples only and should be replaced for real deployments.

## Current Status

- Public EC2 deployment: complete
- HTTPS and custom subdomain: complete
- Docker Compose production stack: complete
- Local Kubernetes deployment: complete
- Argo CD GitOps: complete
- Kubernetes self-healing demo: complete
- GitOps self-healing demo: complete
- Prometheus/Grafana/Loki: planned future improvement

