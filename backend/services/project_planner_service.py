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
    }

    return ProjectDetailsResponse.model_validate(details).model_dump(mode="json")
