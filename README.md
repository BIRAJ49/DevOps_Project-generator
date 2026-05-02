# ProjectOps

ProjectOps is a full-stack project idea planner and starter-bundle generator. It suggests practical software projects from a local template catalog, expands selected ideas into implementation plans, and can package predefined DevOps starter templates as ZIP and PDF artifacts.

The app is designed to work without an external AI provider. Project suggestions come from `templates/project_ideas/catalog.json`, which currently supports a broad set of DevOps, cloud, backend, frontend, mobile, AI, data, security, testing, payment, and app-building topics.

## What It Does

- Suggests project ideas for a user-entered topic or stack.
- Returns different ideas across repeated requests when possible.
- Supports 50 idea blueprints per catalog topic.
- Expands a selected idea into architecture, tools, implementation steps, deliverables, and risks.
- Provides predefined downloadable starter bundles for Docker, Kubernetes, CI/CD, and Terraform.
- Supports guest usage limits and authenticated unlimited usage.
- Stores users, usage records, and generated artifact metadata in PostgreSQL.
- Can store generated artifacts locally or in private S3-compatible storage.

## Tech Stack

- Backend: FastAPI, SQLAlchemy, PostgreSQL, Pydantic, JWT, bcrypt
- Frontend: React, Vite, React Router, Tailwind CSS, lucide-react
- Templates: local JSON/YAML/Terraform/Docker/Python/Node template files
- Artifacts: ZIP and PDF generation, local filesystem or S3 storage
- Infrastructure: Docker Compose for local PostgreSQL

## Project Structure

```text
DevOps_Project_generator/
├── backend/
│   ├── auth/                 # JWT auth and password security
│   ├── models/               # SQLAlchemy models and runtime migrations
│   ├── routes/               # FastAPI route modules
│   ├── services/             # planner, templates, artifacts, email, usage
│   ├── utils/                # config, schemas, rate limiting, request helpers
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── templates/
│   ├── cicd/
│   ├── docker/
│   ├── kubernetes/
│   ├── project_ideas/
│   └── terraform/
├── docker-compose.yml
├── .env.example
└── README.md
```

## Template Catalog

ProjectOps has two template layers:

- `templates/project_ideas/catalog.json`: topic-based idea suggestions. A normal suggestion request returns 3 ideas; a request such as `50 Kubernetes ideas` returns the full 50-idea set for that topic.
- `templates/{docker,kubernetes,cicd,terraform}/{beginner,intermediate,advanced}`: downloadable starter project bundles used by the `/api/generate` flow.

The idea catalog includes aliases for common variations such as `cicd`, `gcp`, `dotnet`, `csharp`, and `e2e testing`.

## Local Development

### 1. Clone and enter the project

```bash
git clone <your-repo-url>
cd DevOps_Project_generator
```

### 2. Create environment files

```bash
cp .env.example .env
```

For local development, set these values in `.env`:

```env
JWT_SECRET_KEY=replace-this-with-at-least-32-characters
DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:5432/devops_project_generator
FRONTEND_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
ARTIFACT_STORAGE_BACKEND=local
```

Optional frontend env:

```bash
cd frontend
printf 'VITE_API_BASE_URL=http://127.0.0.1:8000\n' > .env
cd ..
```

### 3. Install backend dependencies

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
```

### 4. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

### 5. Start PostgreSQL

```bash
docker compose up -d postgres
```

### 6. Start the backend

```bash
.venv/bin/uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Backend health check:

```bash
curl http://127.0.0.1:8000/health
```

### 7. Start the frontend

In a second terminal:

```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

Open `http://127.0.0.1:5173`.

## API Overview

### Auth

- `POST /api/signup`
- `POST /api/verify-email`
- `POST /api/resend-verification`
- `POST /api/login`
- `GET /api/me`
- `POST /api/forgot-password`
- `POST /api/reset-password`

### Planning

- `POST /api/suggest`
- `POST /api/details`

Example suggestion request:

```bash
curl -X POST http://127.0.0.1:8000/api/suggest \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"React"}'
```

Example full catalog request:

```bash
curl -X POST http://127.0.0.1:8000/api/suggest \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"50 AWS project ideas"}'
```

### Starter Bundle Generation

- `POST /api/generate`
- `GET /api/generate/{generation_id}/download/zip`
- `GET /api/generate/{generation_id}/download/pdf`

Example:

```bash
curl -X POST http://127.0.0.1:8000/api/generate \
  -H 'Content-Type: application/json' \
  -d '{"project_type":"docker","difficulty_level":"beginner"}'
```

Valid `project_type` values:

- `docker`
- `kubernetes`
- `cicd`
- `terraform`

Valid `difficulty_level` values:

- `beginner`
- `intermediate`
- `advanced`

## Environment Variables

Root `.env` is loaded by the backend.

| Variable | Required | Purpose |
| --- | --- | --- |
| `JWT_SECRET_KEY` | Yes | Secret used to sign JWT access tokens. Must be at least 32 characters. |
| `JWT_ALGORITHM` | No | JWT signing algorithm. Defaults to `HS256`. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Access token lifetime. Defaults to `60`. |
| `DATABASE_URL` | Yes | PostgreSQL SQLAlchemy connection URL. |
| `FRONTEND_ORIGINS` | No | Comma-separated allowed browser origins. |
| `TRUSTED_PROXY_IPS` | No | Proxy IPs trusted for forwarded client IP headers. |
| `RESEND_API_KEY` | No | Enables real email delivery through Resend. |
| `EMAIL_FROM` | No | Sender used for verification and password reset emails. |
| `CONTACT_RECIPIENT_EMAIL` | No | Inbox that receives contact form messages. Defaults to `terms301@gmail.com`. |
| `EMAIL_VERIFICATION_CODE_TTL_MINUTES` | No | Verification code lifetime. |
| `EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS` | No | Cooldown before another verification code can be sent. |
| `EMAIL_VERIFICATION_MAX_ATTEMPTS` | No | Maximum failed verification attempts per code. |
| `GUEST_PROJECT_LIMIT` | No | Number of allowed guest requests. Defaults to `3`. |
| `RATE_LIMIT_WINDOW_SECONDS` | No | API rate limit window. |
| `RATE_LIMIT_MAX_REQUESTS` | No | General API requests allowed per window. |
| `AUTH_RATE_LIMIT_MAX_REQUESTS` | No | Auth requests allowed per window. |
| `RATE_LIMIT_MAX_BUCKETS` | No | Maximum in-memory rate limit buckets. |
| `ARTIFACT_STORAGE_BACKEND` | No | `local` or `s3`. Defaults to `local`. |
| `ARTIFACT_DOWNLOAD_TTL_SECONDS` | No | Presigned S3 download URL lifetime. |
| `AWS_REGION` | Required for S3 | Region for S3 artifact storage. |
| `S3_BUCKET_NAME` | Required for S3 | Private bucket for generated artifacts. |
| `S3_ARTIFACT_PREFIX` | No | Prefix for artifact keys. |
| `S3_ENDPOINT_URL` | No | Custom S3-compatible endpoint. |

Frontend `frontend/.env`:

| Variable | Required | Purpose |
| --- | --- | --- |
| `VITE_API_BASE_URL` | No | Backend base URL. Use `http://127.0.0.1:8000` locally. |

## Artifact Storage

Use local artifact storage for development:

```env
ARTIFACT_STORAGE_BACKEND=local
```

Generated ZIP and PDF files are written to `generated/`.

Use S3-compatible storage for deployment:

```env
ARTIFACT_STORAGE_BACKEND=s3
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-private-artifact-bucket
S3_ARTIFACT_PREFIX=generated-projects
```

Keep the bucket private. Downloads are served through presigned URLs.

## Email Behavior

The auth flow supports email verification and password reset codes. Configure `RESEND_API_KEY` and `EMAIL_FROM` for real email delivery.

If email delivery is not configured, review the backend email service behavior before relying on signup verification in a deployed environment.

## Security Notes

- Passwords are hashed with bcrypt.
- JWTs expire according to `ACCESS_TOKEN_EXPIRE_MINUTES`.
- CORS is restricted through `FRONTEND_ORIGINS`.
- Forwarded IP headers are trusted only for configured `TRUSTED_PROXY_IPS`.
- Template loading is restricted to the local `templates/` directory.
- Generated artifacts should not contain secrets.
- Keep `.env` out of version control.

## Development Commands

Backend compile check:

```bash
JWT_SECRET_KEY=replace-this-with-at-least-32-characters \
  .venv/bin/python -m compileall backend
```

Frontend build:

```bash
cd frontend
npm run build
```

Frontend lint:

```bash
cd frontend
npm run lint
```

Stop local PostgreSQL:

```bash
docker compose down
```

Remove local PostgreSQL data:

```bash
docker compose down -v
```

## Deployment Checklist

- Set a strong `JWT_SECRET_KEY`.
- Use a managed PostgreSQL database and update `DATABASE_URL`.
- Set production `FRONTEND_ORIGINS`.
- Configure email delivery if public signup is enabled.
- Use `ARTIFACT_STORAGE_BACKEND=s3` for stateless deployments.
- Keep S3 buckets private and use least-privilege IAM.
- Run frontend build and backend startup checks before release.
- Review guest limits and rate limits for expected traffic.

## License

Add your project license here before publishing the repository.
