# DevOps Project Generator

DevOps Project Generator is a SaaS-style full-stack app that generates locally stored DevOps starter projects for Docker, Kubernetes, CI/CD, and Terraform across beginner, intermediate, and advanced difficulty levels.

## Features
- Guest users can generate up to 3 projects based on IP tracking.
- Authenticated users can generate without the guest cap.
- JWT authentication with bcrypt password hashing.
- PostgreSQL persistence through SQLAlchemy ORM.
- Basic API rate limiting and origin-restricted CORS.
- Local template library with ZIP and PDF downloads for generated bundles.
- Artifact storage that can run locally or upload to private S3 with presigned downloads.

## Project Structure
```text
DevOps_Project_generator/
├── backend/
│   ├── auth/
│   ├── models/
│   ├── routes/
│   ├── services/
│   ├── utils/
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── public/
│   ├── .env.example
│   └── package.json
├── templates/
│   ├── docker/
│   ├── kubernetes/
│   ├── cicd/
│   └── terraform/
├── .env.example
└── README.md
```

## Backend API
- `POST /api/signup`
- `POST /api/login`
- `GET /api/me`
- `POST /api/generate`
- `GET /api/generate/{generation_id}/download/zip`
- `GET /api/generate/{generation_id}/download/pdf`
- `GET /health`

## Security Notes
- Only predefined `project_type` and `difficulty_level` enum values are accepted.
- Templates are served only from the local `templates/` directory.
- Passwords are hashed with bcrypt and never stored in plaintext.
- JWT tokens expire after 1 hour by default.
- CORS origins come from environment configuration.
- Secrets are stored in `.env`, with committed placeholders in `.env.example`.

## Local Development
1. Create a Python virtual environment:
   `python3 -m venv .venv`
2. Install backend dependencies:
   `.venv/bin/pip install -r backend/requirements.txt`
3. Install frontend dependencies:
   `cd frontend && npm install`
4. Start local PostgreSQL:
   `docker compose up -d postgres`
5. Start the backend from the repository root:
   `.venv/bin/uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000`
6. Start the frontend in a second terminal:
   `cd frontend && npm run dev -- --host 127.0.0.1 --port 5173`

## Environment Variables
Root `.env`:
- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `DATABASE_URL`
- `FRONTEND_ORIGINS`
- `GUEST_PROJECT_LIMIT`
- `RATE_LIMIT_WINDOW_SECONDS`
- `RATE_LIMIT_MAX_REQUESTS`
- `AUTH_RATE_LIMIT_MAX_REQUESTS`
- `ARTIFACT_STORAGE_BACKEND`
- `ARTIFACT_DOWNLOAD_TTL_SECONDS`
- `AWS_REGION`
- `S3_BUCKET_NAME`
- `S3_ARTIFACT_PREFIX`
- `S3_ENDPOINT_URL`

Frontend `frontend/.env`:
- `VITE_API_BASE_URL`

## PostgreSQL Notes
- The default local development connection string points to the PostgreSQL container in `docker-compose.yml`.
- For deployment, replace `DATABASE_URL` with your managed PostgreSQL connection string.
- If your provider requires TLS, include the provider-specific query parameters in the URL, such as `sslmode=require` when applicable.

## Artifact Storage Notes
- Use `ARTIFACT_STORAGE_BACKEND=local` for local development.
- Use `ARTIFACT_STORAGE_BACKEND=s3` in deployment if you want stateless artifact downloads.
- Keep the S3 bucket private and use presigned URLs for downloads.
- ZIP files contain the starter project files.
- PDF files contain the generated project brief, implementation summary, and artifact inventory.

## Template Coverage
- Docker: beginner, intermediate, advanced
- Kubernetes: beginner, intermediate, advanced
- CI/CD: beginner, intermediate, advanced
- Terraform: beginner, intermediate, advanced

## Notes
- No external API keys are required for local development.
- Terraform and CI/CD templates intentionally use placeholders for cloud roles, image tags, and deployment hosts.
- Local artifacts are written to `generated/` when `ARTIFACT_STORAGE_BACKEND=local`.
