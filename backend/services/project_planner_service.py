from typing import Any

from backend.services.project_idea_catalog import (
    clean_category,
    suggestions_for_prompt,
)
from backend.utils.schemas import DifficultyLevel, ProjectDetailsResponse

SUGGESTION_DIFFICULTY_ORDER = (
    DifficultyLevel.beginner.value,
    DifficultyLevel.intermediate.value,
    DifficultyLevel.advanced.value,
)


TOOLS_BY_CATEGORY = {
    "docker": ["Docker", "Docker Compose", "FastAPI", "Redis", "Make"],
    "kubernetes": ["kubectl", "Kubernetes", "Ingress Controller", "HPA", "Helm"],
    "cicd": ["GitHub Actions", "Docker", "pytest", "Trivy", "Deployment scripts"],
    "github_actions": ["GitHub Actions", "Docker", "pytest", "Trivy", "Deployment scripts"],
    "gitlab_ci_cd": ["GitLab CI/CD", "Docker", "pytest", "Container registry", "Deployment scripts"],
    "jenkins": ["Jenkins", "Docker", "Pipeline as Code", "Credentials store", "Deployment scripts"],
    "terraform": ["Terraform", "AWS provider", "Remote state", "tfvars", "tflint"],
    "ansible": ["Ansible", "YAML", "Inventory files", "Jinja templates", "Molecule"],
    "aws": ["AWS IAM", "S3", "ECS or Lambda", "CloudWatch", "AWS CLI"],
    "azure": ["Azure CLI", "Azure App Service", "Azure Monitor", "Key Vault", "Bicep or Terraform"],
    "google_cloud": ["Google Cloud CLI", "Cloud Run", "Cloud Storage", "Cloud Monitoring", "Terraform"],
    "linux": ["Bash", "systemd", "cron", "rsync", "journalctl"],
    "shell_scripting": ["Bash", "shellcheck", "cron", "systemd", "Make"],
    "monitoring": ["Prometheus", "Grafana", "Alertmanager", "Node Exporter", "Loki"],
    "prometheus": ["Prometheus", "Alertmanager", "PromQL", "Node Exporter", "Grafana"],
    "grafana": ["Grafana", "Prometheus", "Loki", "Dashboards as Code", "Alerting"],
    "react": ["React", "TypeScript", "Vite", "React Router", "Testing Library"],
    "next_js": ["Next.js", "TypeScript", "PostgreSQL", "Prisma", "Vercel"],
    "vue_js": ["Vue.js", "TypeScript", "Vite", "Pinia", "Vitest"],
    "angular": ["Angular", "TypeScript", "RxJS", "Angular Material", "Karma or Jest"],
    "svelte": ["Svelte", "SvelteKit", "TypeScript", "Vite", "Playwright"],
    "node_js": ["Node.js", "Express.js", "PostgreSQL", "Redis", "Vitest"],
    "express_js": ["Express.js", "Node.js", "JWT", "PostgreSQL", "Supertest"],
    "fastapi": ["FastAPI", "Pydantic", "SQLAlchemy", "PostgreSQL", "pytest"],
    "django": ["Django", "Django REST Framework", "PostgreSQL", "Celery", "pytest"],
    "flask": ["Flask", "SQLAlchemy", "PostgreSQL", "pytest", "Gunicorn"],
    "spring_boot": ["Spring Boot", "Java", "Maven or Gradle", "PostgreSQL", "JUnit"],
    "python": ["Python", "FastAPI or Flask", "pytest", "PostgreSQL", "Docker"],
    "java": ["Java", "Spring Boot", "Maven or Gradle", "PostgreSQL", "JUnit"],
    "go": ["Go", "Gin or Chi", "PostgreSQL", "Docker", "go test"],
    "rust": ["Rust", "Axum or Actix", "SQLx", "PostgreSQL", "cargo test"],
    "typescript": ["TypeScript", "Node.js", "ESLint", "Vitest", "Playwright"],
    "javascript": ["JavaScript", "Node.js", "ESLint", "Vitest", "Playwright"],
    "postgresql": ["PostgreSQL", "SQL", "pgAdmin", "Migration tooling", "Backups"],
    "mongodb": ["MongoDB", "Mongoose or native driver", "Indexes", "Change streams", "Backups"],
    "redis": ["Redis", "Queues", "Caching", "Rate limiting", "Monitoring"],
    "ai_chatbot": ["LLM API", "Vector database", "Prompt templates", "RAG", "Evaluation scripts"],
    "machine_learning": ["Python", "scikit-learn", "Pandas", "MLflow", "Jupyter"],
    "mlops": ["MLflow", "Docker", "Model registry", "CI/CD", "Monitoring"],
    "stripe": ["Stripe API", "Webhooks", "PostgreSQL", "RBAC", "Audit logs"],
    "khalti": ["Khalti API", "Webhooks", "PostgreSQL", "Payment status checks", "Audit logs"],
    "esewa": ["Esewa API", "Webhooks", "PostgreSQL", "Payment verification", "Audit logs"],
    "game_development": ["Game engine", "Asset pipeline", "Input system", "Physics", "Build tooling"],
    "testing": ["pytest or Vitest", "Playwright", "Postman", "CI checks", "Coverage reports"],
}

DEFAULT_TOOLS = [
    "Git",
    "Relevant language runtime and package manager",
    "Database or storage layer when needed",
    "Test runner",
    "Docker or local development scripts",
    "README and architecture notes",
]


def _difficulty_scope(difficulty: str) -> dict[str, str]:
    scopes = {
        DifficultyLevel.beginner.value: {
            "setup": "Keep the first version small, local, and easy to run from one command.",
            "quality": "Cover the main happy path and one failure path with focused tests.",
            "deployment": "Deploy a single service or static app with clear environment variables.",
        },
        DifficultyLevel.intermediate.value: {
            "setup": "Use separate frontend, backend, database, and local automation where useful.",
            "quality": "Add integration tests, seed data, linting, and repeatable CI checks.",
            "deployment": "Containerize the app and document rollback, logs, and config changes.",
        },
        DifficultyLevel.advanced.value: {
            "setup": "Design for production concerns: auth, observability, background work, and scaling.",
            "quality": "Add contract tests, end-to-end tests, security checks, and measurable acceptance criteria.",
            "deployment": "Use infrastructure as code, staged rollout, monitoring, and recovery notes.",
        },
    }
    return scopes.get(difficulty, scopes[DifficultyLevel.beginner.value])


def _platform_shape(category: str) -> dict[str, str]:
    if category in {"react", "vue_js", "angular", "svelte", "next_js"}:
        return {
            "frontend": "Build the primary screen, routing, form states, loading states, and empty states first.",
            "backend": "Add a small API only if the project needs persistence, auth, or server-side integrations.",
            "storage": "Use local fixtures first, then add a database or API-backed state once the UI flow is clear.",
        }
    if category in {"fastapi", "node_js", "express_js", "django", "flask", "spring_boot", "go", "rust"}:
        return {
            "frontend": "Add a lightweight client or API docs page so the workflow can be tested manually.",
            "backend": "Model resources, endpoints, validation, service functions, and error responses.",
            "storage": "Start with one durable store, migrations, seed data, and backup/export notes.",
        }
    if category in {"docker", "kubernetes", "cicd", "github_actions", "gitlab_ci_cd", "jenkins", "terraform", "ansible"}:
        return {
            "frontend": "Use a simple demo app, dashboard, or generated report as the visible outcome.",
            "backend": "Keep orchestration scripts idempotent and expose status through logs or reports.",
            "storage": "Store generated artifacts, logs, state files, or sample outputs in predictable paths.",
        }
    if category in {"aws", "azure", "google_cloud", "monitoring", "prometheus", "grafana", "mlops"}:
        return {
            "frontend": "Show operational status through a dashboard, README screenshots, or generated report.",
            "backend": "Automate provisioning, checks, alert rules, and cleanup tasks through scripts.",
            "storage": "Document state, metrics, logs, secrets, and retention assumptions.",
        }
    return {
        "frontend": "Create the smallest interface that proves the main user workflow.",
        "backend": "Add server-side logic for validation, persistence, integrations, and permissions.",
        "storage": "Choose the simplest storage layer that preserves the project’s important state.",
    }


def _build_milestones(title: str, category: str, difficulty: str) -> list[dict[str, list[str] | str]]:
    scope = _difficulty_scope(difficulty)
    platform = _platform_shape(category)
    return [
        {
            "title": "1. Define scope and acceptance criteria",
            "goal": f"Turn {title} into a buildable project with a clear first release.",
            "steps": [
                "Write the target user, problem statement, and one primary workflow.",
                "List must-have features, nice-to-have features, and out-of-scope ideas.",
                "Create acceptance criteria for setup, core behavior, errors, and demo readiness.",
                scope["setup"],
            ],
            "verification": [
                "A README draft explains what the project does and how success is measured.",
                "The first version can be described in five to seven concrete tasks.",
            ],
        },
        {
            "title": "2. Set up the repository and local environment",
            "goal": "Make the project reproducible before implementing business logic.",
            "steps": [
                "Create the app folders, package files, environment example, and gitignore.",
                "Add a local run command and document required runtime versions.",
                "Prepare sample data, seed scripts, or mock responses for early development.",
                "Add formatting, linting, and a basic smoke test command.",
            ],
            "verification": [
                "A new developer can install dependencies and start the project from the README.",
                "The smoke test passes before feature work begins.",
            ],
        },
        {
            "title": "3. Build the core workflow",
            "goal": "Implement the smallest end-to-end version that proves the idea.",
            "steps": [
                platform["frontend"],
                platform["backend"],
                platform["storage"],
                "Handle validation errors, empty results, loading states, and retryable failures.",
            ],
            "verification": [
                "The main workflow works with realistic sample inputs.",
                "Failure states produce useful messages instead of silent errors.",
            ],
        },
        {
            "title": "4. Add tests and quality checks",
            "goal": "Protect the project from regressions before adding polish.",
            "steps": [
                "Add unit tests around parsing, validation, and service logic.",
                "Add an integration or end-to-end test for the primary workflow.",
                "Run linting, formatting, and security checks in a single command.",
                scope["quality"],
            ],
            "verification": [
                "The documented test command passes from a clean checkout.",
                "At least one test covers an expected failure case.",
            ],
        },
        {
            "title": "5. Prepare deployment and documentation",
            "goal": "Make the project demo-ready and understandable after handoff.",
            "steps": [
                "Write setup, run, test, deploy, environment, and troubleshooting sections.",
                "Add Docker, CI/CD, or hosting config that matches the selected stack.",
                "Document logs, health checks, secret handling, and rollback steps.",
                scope["deployment"],
            ],
            "verification": [
                "Deployment steps have been tested or clearly marked as provider-specific.",
                "The README includes screenshots, API examples, or demo data.",
            ],
        },
    ]


def _build_file_structure(category: str) -> list[dict[str, str]]:
    common = [
        {"path": "README.md", "purpose": "Project overview, setup, run, test, deploy, and troubleshooting notes."},
        {"path": ".env.example", "purpose": "Document required local and deployment environment variables."},
        {"path": "tests/", "purpose": "Unit, integration, or end-to-end tests for the main workflow."},
        {"path": "docs/architecture.md", "purpose": "Architecture, data flow, assumptions, and extension notes."},
    ]
    if category in {"react", "vue_js", "angular", "svelte", "next_js", "typescript", "javascript"}:
        return [
            {"path": "src/pages/", "purpose": "Route-level screens for the main workflow."},
            {"path": "src/components/", "purpose": "Reusable UI controls, forms, tables, and feedback states."},
            {"path": "src/api/", "purpose": "API client functions and response normalization."},
            {"path": "src/state/", "purpose": "Shared state, hooks, stores, or context providers."},
            *common,
        ]
    if category in {"fastapi", "python", "flask", "django"}:
        return [
            {"path": "app/main.py", "purpose": "Application entry point, middleware, and route registration."},
            {"path": "app/routes/", "purpose": "HTTP endpoints grouped by resource or workflow."},
            {"path": "app/services/", "purpose": "Business logic that is testable outside the web layer."},
            {"path": "app/models/", "purpose": "Database models, schemas, and migration helpers."},
            *common,
        ]
    if category in {"node_js", "express_js"}:
        return [
            {"path": "src/server.ts", "purpose": "Server startup, middleware, and health check."},
            {"path": "src/routes/", "purpose": "Express routers grouped by feature."},
            {"path": "src/services/", "purpose": "Business logic and external integrations."},
            {"path": "src/db/", "purpose": "Database client, migrations, and seed data."},
            *common,
        ]
    if category in {"docker", "kubernetes", "cicd", "github_actions", "gitlab_ci_cd", "jenkins", "terraform", "ansible"}:
        return [
            {"path": "app/", "purpose": "Small demo service or script used to prove the workflow."},
            {"path": "infra/", "purpose": "Docker, Kubernetes, Terraform, Ansible, or CI/CD configuration."},
            {"path": "scripts/", "purpose": "Repeatable setup, validation, deployment, and cleanup commands."},
            {"path": "reports/", "purpose": "Generated status output, scan results, or deployment notes."},
            *common,
        ]
    return [
        {"path": "src/", "purpose": "Application source code organized by feature."},
        {"path": "config/", "purpose": "Runtime configuration, examples, and local defaults."},
        {"path": "scripts/", "purpose": "Setup, validation, demo, and maintenance commands."},
        *common,
    ]


def _build_api_contracts(category: str) -> list[dict[str, str]]:
    if category in {"docker", "kubernetes", "cicd", "terraform", "ansible", "monitoring", "prometheus", "grafana"}:
        return [
            {"method": "GET", "path": "/health", "purpose": "Return service status for local checks and deployment probes."},
            {"method": "POST", "path": "/api/jobs", "purpose": "Start the main automation, scan, generation, or deployment workflow."},
            {"method": "GET", "path": "/api/jobs/{job_id}", "purpose": "Read workflow status, logs, results, and next actions."},
        ]
    return [
        {"method": "GET", "path": "/health", "purpose": "Return service status for smoke tests and monitoring."},
        {"method": "GET", "path": "/api/items", "purpose": "List the main resources for the project."},
        {"method": "POST", "path": "/api/items", "purpose": "Create or trigger the primary user workflow."},
        {"method": "GET", "path": "/api/items/{item_id}", "purpose": "Fetch details, status, history, or generated output."},
    ]


def _build_data_model(category: str) -> list[dict[str, str | list[str]]]:
    if category in {"docker", "kubernetes", "cicd", "terraform", "ansible"}:
        return [
            {"name": "ProjectRun", "fields": ["id", "type", "status", "started_at", "completed_at", "summary"], "notes": "Tracks each generated bundle, deployment, scan, or automation run."},
            {"name": "RunArtifact", "fields": ["id", "run_id", "path", "kind", "created_at"], "notes": "Stores links to reports, archives, logs, and generated config files."},
        ]
    return [
        {"name": "User", "fields": ["id", "email", "role", "created_at"], "notes": "Add only if the project needs saved state, ownership, or permissions."},
        {"name": "ProjectItem", "fields": ["id", "title", "status", "metadata", "created_at", "updated_at"], "notes": "Represents the primary resource created or managed by the app."},
        {"name": "ActivityLog", "fields": ["id", "item_id", "event", "details", "created_at"], "notes": "Useful for audit trails, debugging, progress history, or notifications."},
    ]


def _build_test_plan(difficulty: str) -> list[str]:
    tests = [
        "Smoke test: install dependencies, start the app, and verify the health or home route.",
        "Core workflow test: complete the main user journey with realistic sample data.",
        "Validation test: submit invalid input and confirm useful errors are returned.",
        "Regression test: cover the most important service function or UI state.",
    ]
    if difficulty in {DifficultyLevel.intermediate.value, DifficultyLevel.advanced.value}:
        tests.extend(
            [
                "Integration test: verify the API and database or external-service boundary together.",
                "CI test: run linting, formatting, tests, and build checks on every push.",
            ]
        )
    if difficulty == DifficultyLevel.advanced.value:
        tests.extend(
            [
                "Security test: check auth boundaries, secret handling, dependency scans, and unsafe inputs.",
                "Operational test: verify logs, metrics, health checks, rollback, and failure recovery.",
            ]
        )
    return tests


def _build_deployment_steps(category: str, difficulty: str) -> list[str]:
    steps = [
        "Create production environment variables from .env.example and keep secrets out of git.",
        "Build the application or container image from a clean checkout.",
        "Run migrations, seed required data, or provision required infrastructure.",
        "Deploy to the chosen target and verify the health check.",
        "Document rollback steps and the logs to inspect if deployment fails.",
    ]
    if category in {"docker", "kubernetes", "cicd", "terraform"} or difficulty == DifficultyLevel.advanced.value:
        steps.insert(2, "Run infrastructure validation such as docker compose config, kubectl dry-run, terraform plan, or CI pipeline validation.")
    return steps


def _build_next_improvements(difficulty: str) -> list[str]:
    improvements = [
        "Add saved projects or user-specific history.",
        "Add import/export so users can share generated plans or artifacts.",
        "Add better analytics around usage, failures, and completion progress.",
    ]
    if difficulty in {DifficultyLevel.intermediate.value, DifficultyLevel.advanced.value}:
        improvements.extend(
            [
                "Add role-based permissions and audit logs.",
                "Add background jobs for long-running generation, scans, or deployments.",
            ]
        )
    if difficulty == DifficultyLevel.advanced.value:
        improvements.extend(
            [
                "Add monitoring dashboards, alerts, and SLO-style success metrics.",
                "Add multi-environment deployment with staging, production, and rollback automation.",
            ]
        )
    return improvements


def _slug_title(title: str) -> str:
    slug = "".join(char.lower() if char.isalnum() else "-" for char in title)
    return "-".join(part for part in slug.split("-") if part)[:48] or "project"


def _build_code_examples(category: str, title: str, difficulty: str) -> list[dict[str, str]]:
    service_name = _slug_title(title)
    example_category = {
        "docker_compose": "docker",
        "containerization": "docker",
        "microservices": "docker",
        "helm_charts": "kubernetes",
        "kubernetes_operators": "kubernetes",
        "argocd": "kubernetes",
        "gitops": "kubernetes",
        "infrastructure_as_code": "terraform",
        "iac": "terraform",
        "prometheus_grafana": "monitoring",
        "observability": "monitoring",
        "logging": "monitoring",
        "elk_stack": "monitoring",
        "loki": "monitoring",
        "cloudwatch": "monitoring",
        "vue_js": "vue_js",
        "angular": "angular",
        "svelte": "svelte",
        "java": "spring_boot",
        "php": "laravel",
        "c": "dotnet",
        "csharp": "dotnet",
        "net": "dotnet",
        "database": "postgresql",
        "sql": "postgresql",
        "mysql": "postgresql",
        "firebase": "postgresql",
        "supabase": "postgresql",
        "stripe": "payment",
        "khalti": "payment",
        "esewa": "payment",
        "payment_integration": "payment",
        "openai_api": "ai_chatbot",
        "gemini_api": "ai_chatbot",
        "openrouter_api": "ai_chatbot",
        "ollama": "ai_chatbot",
        "hugging_face": "machine_learning",
        "rag": "ai_chatbot",
        "vector_database": "ai_chatbot",
        "langchain": "ai_chatbot",
        "data_analysis": "machine_learning",
        "data_visualization": "machine_learning",
        "deep_learning": "machine_learning",
        "generative_ai": "ai_chatbot",
        "unit_testing": "testing",
        "integration_testing": "testing",
        "end_to_end_testing": "testing",
        "playwright": "testing",
        "selenium": "testing",
        "postman": "testing",
        "api_testing": "testing",
        "performance_testing": "testing",
        "load_testing": "testing",
    }.get(category, category)
    common_app = {
        "path": "app/main.py",
        "language": "python",
        "content": '''from fastapi import FastAPI

app = FastAPI(title="Project service")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/items")
def list_items() -> list[dict[str, str]]:
    return [{"id": "demo", "status": "ready"}]
''',
    }

    examples_by_category: dict[str, list[dict[str, str]]] = {
        "docker": [
            {
                "path": "Dockerfile",
                "language": "dockerfile",
                "content": '''FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
''',
            },
            {
                "path": "docker-compose.yml",
                "language": "yaml",
                "content": '''services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      APP_ENV: development
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 5s
      retries: 3
''',
            },
            common_app,
        ],
        "kubernetes": [
            {
                "path": "k8s/deployment.yaml",
                "language": "yaml",
                "content": f'''apiVersion: apps/v1
kind: Deployment
metadata:
  name: {service_name}
spec:
  replicas: 2
  selector:
    matchLabels:
      app: {service_name}
  template:
    metadata:
      labels:
        app: {service_name}
    spec:
      containers:
        - name: api
          image: {service_name}:latest
          ports:
            - containerPort: 8000
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
''',
            },
            {
                "path": "k8s/service.yaml",
                "language": "yaml",
                "content": f'''apiVersion: v1
kind: Service
metadata:
  name: {service_name}
spec:
  selector:
    app: {service_name}
  ports:
    - port: 80
      targetPort: 8000
''',
            },
        ],
        "cicd": [
            {
                "path": ".github/workflows/ci.yml",
                "language": "yaml",
                "content": '''name: ci

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt
      - run: pytest
      - run: docker build -t project-app:${{ github.sha }} .
''',
            },
            common_app,
        ],
        "github_actions": [
            {
                "path": ".github/workflows/build-test.yml",
                "language": "yaml",
                "content": '''name: build-test

on:
  push:
  pull_request:

jobs:
  checks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
      - run: npm ci
      - run: npm run lint
      - run: npm test -- --run
      - run: npm run build
''',
            }
        ],
        "gitlab_ci_cd": [
            {
                "path": ".gitlab-ci.yml",
                "language": "yaml",
                "content": '''stages:
  - test
  - build

test:
  image: python:3.12
  stage: test
  script:
    - pip install -r requirements.txt
    - pytest

container:
  image: docker:27
  services:
    - docker:27-dind
  stage: build
  script:
    - docker build -t "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA" .
''',
            }
        ],
        "jenkins": [
            {
                "path": "Jenkinsfile",
                "language": "groovy",
                "content": '''pipeline {
  agent any

  stages {
    stage('Install') {
      steps { sh 'pip install -r requirements.txt' }
    }
    stage('Test') {
      steps { sh 'pytest' }
    }
    stage('Build Image') {
      steps { sh 'docker build -t project-app:${BUILD_NUMBER} .' }
    }
  }
}
''',
            }
        ],
        "terraform": [
            {
                "path": "main.tf",
                "language": "hcl",
                "content": '''terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

resource "aws_s3_bucket" "artifacts" {
  bucket = var.artifact_bucket_name
}
''',
            },
            {
                "path": "variables.tf",
                "language": "hcl",
                "content": '''variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "artifact_bucket_name" {
  type        = string
  description = "Globally unique bucket for generated artifacts."
}
''',
            },
        ],
        "ansible": [
            {
                "path": "playbooks/site.yml",
                "language": "yaml",
                "content": '''- name: Configure application host
  hosts: app
  become: true
  tasks:
    - name: Install packages
      ansible.builtin.apt:
        name:
          - docker.io
          - nginx
        state: present
        update_cache: true

    - name: Ensure nginx is running
      ansible.builtin.service:
        name: nginx
        state: started
        enabled: true
''',
            }
        ],
        "react": [
            {
                "path": "src/App.jsx",
                "language": "jsx",
                "content": '''import { useEffect, useState } from "react";

export default function App() {
  const [items, setItems] = useState([]);

  useEffect(() => {
    fetch("/api/items")
      .then((response) => response.json())
      .then(setItems);
  }, []);

  return (
    <main>
      <h1>Project dashboard</h1>
      {items.map((item) => (
        <article key={item.id}>{item.status}</article>
      ))}
    </main>
  );
}
''',
            }
        ],
        "vue_js": [
            {
                "path": "src/App.vue",
                "language": "vue",
                "content": '''<script setup>
import { onMounted, ref } from "vue";

const items = ref([]);

onMounted(async () => {
  items.value = await fetch("/api/items").then((response) => response.json());
});
</script>

<template>
  <main>
    <h1>Project dashboard</h1>
    <article v-for="item in items" :key="item.id">
      {{ item.status }}
    </article>
  </main>
</template>
''',
            }
        ],
        "angular": [
            {
                "path": "src/app/app.component.ts",
                "language": "typescript",
                "content": '''import { Component, inject } from "@angular/core";
import { HttpClient } from "@angular/common/http";

@Component({
  selector: "app-root",
  template: `
    <main>
      <h1>Project dashboard</h1>
      <article *ngFor="let item of items">{{ item.status }}</article>
    </main>
  `,
})
export class AppComponent {
  private http = inject(HttpClient);
  items: Array<{ id: string; status: string }> = [];

  ngOnInit() {
    this.http.get<Array<{ id: string; status: string }>>("/api/items").subscribe((items) => {
      this.items = items;
    });
  }
}
''',
            }
        ],
        "svelte": [
            {
                "path": "src/routes/+page.svelte",
                "language": "svelte",
                "content": '''<script>
  import { onMount } from "svelte";

  let items = [];

  onMount(async () => {
    items = await fetch("/api/items").then((response) => response.json());
  });
</script>

<main>
  <h1>Project dashboard</h1>
  {#each items as item}
    <article>{item.status}</article>
  {/each}
</main>
''',
            }
        ],
        "next_js": [
            {
                "path": "app/page.tsx",
                "language": "tsx",
                "content": '''export default async function Page() {
  const items = await fetch("http://localhost:3000/api/items", {
    cache: "no-store",
  }).then((response) => response.json());

  return (
    <main>
      <h1>Project workspace</h1>
      <pre>{JSON.stringify(items, null, 2)}</pre>
    </main>
  );
}
''',
            }
        ],
        "node_js": [
            {
                "path": "src/server.ts",
                "language": "typescript",
                "content": '''import express from "express";

const app = express();
app.use(express.json());

app.get("/health", (_req, res) => {
  res.json({ status: "ok" });
});

app.post("/api/jobs", (req, res) => {
  res.status(202).json({ id: crypto.randomUUID(), input: req.body });
});

app.listen(3000, () => console.log("API listening on :3000"));
''',
            }
        ],
        "express_js": [
            {
                "path": "src/server.ts",
                "language": "typescript",
                "content": '''import express from "express";

const app = express();
app.use(express.json());

app.get("/api/items", (_req, res) => {
  res.json([{ id: "demo", status: "ready" }]);
});

app.listen(3000);
''',
            }
        ],
        "fastapi": [common_app],
        "python": [common_app],
        "flask": [
            {
                "path": "app.py",
                "language": "python",
                "content": '''from flask import Flask, jsonify, request

app = Flask(__name__)


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.post("/api/jobs")
def create_job():
    return jsonify(id="demo-job", input=request.json), 202
''',
            }
        ],
        "django": [
            {
                "path": "project/urls.py",
                "language": "python",
                "content": '''from django.http import JsonResponse
from django.urls import path


def health(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("health", health),
]
''',
            }
        ],
        "spring_boot": [
            {
                "path": "src/main/java/com/example/HealthController.java",
                "language": "java",
                "content": '''package com.example;

import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class HealthController {
  @GetMapping("/health")
  public Map<String, String> health() {
    return Map.of("status", "ok");
  }
}
''',
            }
        ],
        "go": [
            {
                "path": "cmd/api/main.go",
                "language": "go",
                "content": '''package main

import (
  "encoding/json"
  "net/http"
)

func main() {
  http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
    json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
  })
  http.ListenAndServe(":8080", nil)
}
''',
            }
        ],
        "rust": [
            {
                "path": "src/main.rs",
                "language": "rust",
                "content": '''use axum::{routing::get, Json, Router};
use serde_json::{json, Value};

async fn health() -> Json<Value> {
    Json(json!({ "status": "ok" }))
}

#[tokio::main]
async fn main() {
    let app = Router::new().route("/health", get(health));
    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000").await.unwrap();
    axum::serve(listener, app).await.unwrap();
}
''',
            }
        ],
        "laravel": [
            {
                "path": "routes/api.php",
                "language": "php",
                "content": '''<?php

use Illuminate\\Support\\Facades\\Route;

Route::get('/health', fn () => ['status' => 'ok']);
Route::get('/items', fn () => [
    ['id' => 'demo', 'status' => 'ready'],
]);
''',
            }
        ],
        "dotnet": [
            {
                "path": "Program.cs",
                "language": "csharp",
                "content": '''var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

app.MapGet("/health", () => Results.Ok(new { status = "ok" }));
app.MapGet("/api/items", () => Results.Ok(new[] { new { id = "demo", status = "ready" } }));

app.Run();
''',
            }
        ],
        "postgresql": [
            {
                "path": "db/schema.sql",
                "language": "sql",
                "content": '''CREATE TABLE project_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'draft',
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX project_items_status_idx ON project_items (status);
''',
            }
        ],
        "mongodb": [
            {
                "path": "src/db/items.js",
                "language": "javascript",
                "content": '''export async function createIndexes(db) {
  await db.collection("project_items").createIndex({ status: 1, createdAt: -1 });
}

export async function listReadyItems(db) {
  return db.collection("project_items").find({ status: "ready" }).toArray();
}
''',
            }
        ],
        "redis": [
            {
                "path": "src/cache.ts",
                "language": "typescript",
                "content": '''import Redis from "ioredis";

const redis = new Redis(process.env.REDIS_URL);

export async function rememberStatus(id: string, status: string) {
  await redis.set(`job:${id}:status`, status, "EX", 3600);
}
''',
            }
        ],
        "payment": [
            {
                "path": "src/payments/webhook.ts",
                "language": "typescript",
                "content": '''export async function handlePaymentWebhook(payload: unknown) {
  // Verify the provider signature before trusting the payload.
  const event = payload as { id: string; type: string };
  return {
    providerEventId: event.id,
    status: event.type,
  };
}
''',
            }
        ],
        "monitoring": [
            {
                "path": "prometheus.yml",
                "language": "yaml",
                "content": '''global:
  scrape_interval: 15s

scrape_configs:
  - job_name: app
    static_configs:
      - targets: ["app:8000"]
''',
            }
        ],
        "prometheus": [
            {
                "path": "prometheus.yml",
                "language": "yaml",
                "content": '''rule_files:
  - alerts.yml

scrape_configs:
  - job_name: node
    static_configs:
      - targets: ["node-exporter:9100"]
''',
            }
        ],
        "grafana": [
            {
                "path": "provisioning/datasources/prometheus.yml",
                "language": "yaml",
                "content": '''apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
''',
            }
        ],
    }

    examples = examples_by_category.get(example_category)
    if examples:
        return examples

    if example_category in {"aws", "azure", "google_cloud"}:
        return [
            {
                "path": "scripts/check-cloud.sh",
                "language": "bash",
                "content": '''#!/usr/bin/env bash
set -euo pipefail

echo "Checking authenticated account"
echo "Checking required environment variables"
echo "Running dry-run validation before deploy"
''',
            },
            {
                "path": ".env.example",
                "language": "dotenv",
                "content": '''CLOUD_REGION=us-east-1
PROJECT_ENV=development
ARTIFACT_BUCKET=
''',
            },
        ]

    if example_category in {"ai_chatbot", "machine_learning", "mlops"}:
        return [
            {
                "path": "src/pipeline.py",
                "language": "python",
                "content": '''def run_pipeline(input_text: str) -> dict[str, str]:
    cleaned = input_text.strip()
    if not cleaned:
        raise ValueError("input_text is required")
    return {
        "status": "completed",
        "summary": cleaned[:160],
    }
''',
            },
            common_app,
        ]

    if example_category in {"testing", "typescript", "javascript"}:
        return [
            {
                "path": "tests/example.test.ts",
                "language": "typescript",
                "content": '''import { describe, expect, it } from "vitest";

describe("core workflow", () => {
  it("returns a ready status", () => {
    expect({ status: "ready" }).toEqual({ status: "ready" });
  });
});
''',
            }
        ]

    return [
        {
            "path": "README.md",
            "language": "markdown",
            "content": f'''# {title}

## Run locally

1. Copy `.env.example` to `.env`.
2. Install dependencies.
3. Start the app and open the health check.

## First workflow

- Build the smallest {format_project_category(category)} feature.
- Add validation and one failure state.
- Add tests before expanding the scope.
''',
        },
        common_app,
    ]


def format_project_category(category: str) -> str:
    return category.replace("_", " ")


def get_project_suggestions(user_prompt: str) -> list[dict[str, str]]:
    return suggestions_for_prompt(user_prompt)


def get_project_details(user_prompt: str, suggestion: dict[str, str]) -> dict[str, Any]:
    category = clean_category(str(suggestion.get("category") or user_prompt))
    difficulty = str(suggestion.get("difficulty_level") or DifficultyLevel.beginner.value)
    if difficulty not in SUGGESTION_DIFFICULTY_ORDER:
        difficulty = DifficultyLevel.beginner.value

    details = {
        "title": str(suggestion.get("title") or "Software project"),
        "category": category,
        "difficulty_level": difficulty,
        "rationale": str(suggestion.get("rationale") or "Aligned to your requested topic."),
        "overview": (
            "Build a practical project with a clear user goal, local setup, core workflow, "
            "validation path, deployment notes, and room to extend the scope."
        ),
        "architecture": [
            "Source repository contains the application, configuration, tests, and documentation.",
            "Core workflow is exposed through a UI, API, CLI, automation job, or integration based on the topic.",
            "Persistence and background processing are added only when the project scope needs them.",
            "Quality checks include linting, tests, sample data, and a reproducible local run command.",
            "Operational notes cover logs, errors, security assumptions, deployment, and rollback.",
        ],
        "recommended_tools": TOOLS_BY_CATEGORY.get(category, DEFAULT_TOOLS),
        "implementation_steps": [
            "Define the target user, main problem, success criteria, and difficulty-appropriate feature scope.",
            "Choose the runtime, framework, data store, and external services required for the topic.",
            "Design the main workflow, data model, permission model, and failure states.",
            "Implement the smallest working version with realistic sample data.",
            "Add validation, error handling, tests, and useful logs before expanding features.",
            "Create a README with setup, run, test, deployment, troubleshooting, and extension notes.",
            "Add one advanced improvement such as automation, analytics, security hardening, or observability.",
        ],
        "deliverables": [
            "Working source repository",
            "Architecture and data-flow notes",
            "Step-by-step implementation plan",
            "Test and validation checklist",
            "Deployment or demo instructions",
            "README outline: overview, prerequisites, setup, run, test, deploy, troubleshoot",
        ],
        "risks": [
            "Scope can grow quickly if the project is not limited to one primary workflow first.",
            "Secrets and API keys must stay in backend environment files or a secret manager.",
            "External services can add cost or rate limits, so cleanup and mock modes should be documented.",
        ],
        "milestones": _build_milestones(str(suggestion.get("title") or "Software project"), category, difficulty),
        "suggested_file_structure": _build_file_structure(category),
        "api_contracts": _build_api_contracts(category),
        "data_model": _build_data_model(category),
        "test_plan": _build_test_plan(difficulty),
        "deployment_steps": _build_deployment_steps(category, difficulty),
        "next_improvements": _build_next_improvements(difficulty),
        "code_examples": _build_code_examples(
            category,
            str(suggestion.get("title") or "Software project"),
            difficulty,
        ),
    }

    return ProjectDetailsResponse.model_validate(details).model_dump(mode="json")
