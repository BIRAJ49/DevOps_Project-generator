import json
import re
import time
from typing import Any
from uuid import uuid4

import httpx
from dotenv import load_dotenv

from backend.services.project_idea_catalog import (
    clean_category as catalog_clean_category,
    suggestions_for_prompt as catalog_suggestions_for_prompt,
)
from backend.services.template_service import TemplateNotFoundError, load_template
from backend.utils.config import BASE_DIR, get_settings
from backend.utils.schemas import DifficultyLevel, ProjectDetailsResponse, ProjectType

SUGGESTION_COUNT = 3
SUGGESTION_DIFFICULTY_ORDER = (
    DifficultyLevel.beginner.value,
    DifficultyLevel.intermediate.value,
    DifficultyLevel.advanced.value,
)
MAX_AI_ATTEMPTS = 3
OPENROUTER_REQUEST_ATTEMPTS = 2
OPENROUTER_CHAT_COMPLETIONS_URL = "https://openrouter.ai/api/v1/chat/completions"
RETRYABLE_OPENROUTER_STATUS_CODES = {429, 500, 502, 503, 504}
OPENROUTER_SYSTEM_PROMPT = (
    "You are a senior DevOps engineer and project planner. Generate practical "
    "DevOps project ideas and detailed implementation plans."
)
FALLBACK_RATE_LIMIT_NOTE = (
    "AI free limit reached, so a template-based project plan was generated."
)
FALLBACK_GENERAL_NOTE = (
    "AI provider unavailable, so a template-based project plan was generated."
)
FALLBACK_INVALID_KEY_NOTE = (
    "Invalid OpenRouter API key, so a template-based project plan was generated."
)
GENERIC_TITLE_PATTERNS = (
    "fundamentals",
    "crud starter",
    "crud app",
    "basic crud",
    "beginner crud",
    "production-ready buildout",
    "advanced capstone",
    "starter app",
    "starter project",
    "todo app",
)
TEMPLATE_PROJECT_KEYWORDS: tuple[tuple[ProjectType, tuple[str, ...]], ...] = (
    (ProjectType.docker, ("docker", "container", "containers", "compose", "image")),
    (ProjectType.kubernetes, ("kubernetes", "k8s", "cluster", "pod", "deployment", "helm")),
    (ProjectType.cicd, ("ci/cd", "cicd", "ci cd", "pipeline", "github actions", "gitlab ci", "deployment automation")),
    (ProjectType.terraform, ("terraform", "iac", "infrastructure as code", "aws", "cloud", "s3", "vpc", "ecs")),
)
DEFAULT_TEMPLATE_SUGGESTIONS: tuple[tuple[ProjectType, DifficultyLevel], ...] = (
    (ProjectType.docker, DifficultyLevel.beginner),
    (ProjectType.kubernetes, DifficultyLevel.intermediate),
    (ProjectType.terraform, DifficultyLevel.advanced),
)


class OpenRouterServiceError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code

    @property
    def fallback_note(self) -> str:
        message = str(self)
        if self.status_code == 429:
            return FALLBACK_RATE_LIMIT_NOTE
        if self.status_code == 401:
            return FALLBACK_INVALID_KEY_NOTE
        if "rate limit" in message.lower():
            return FALLBACK_RATE_LIMIT_NOTE
        if "invalid openrouter api key" in message.lower():
            return FALLBACK_INVALID_KEY_NOTE
        return FALLBACK_GENERAL_NOTE


CATEGORY_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("full_stack_web_app", ("full stack", "fullstack", "react node", "mern", "next.js", "nextjs")),
    ("frontend_web_app", ("react", "vue", "angular", "svelte", "frontend", "tailwind")),
    ("backend_api", ("node", "express", "api", "backend", "django", "fastapi", "spring")),
    ("mobile_app", ("mobile", "android", "ios", "react native", "flutter")),
    ("ai_ml_project", ("ai", "machine learning", "ml", "llm", "chatbot", "computer vision")),
    ("data_project", ("data", "analytics", "dashboard", "etl", "warehouse", "pipeline")),
    ("game_project", ("game", "unity", "godot", "phaser")),
    ("ecommerce_project", ("ecommerce", "e-commerce", "shop", "store", "marketplace")),
    ("automation_tool", ("automation", "script", "bot", "workflow")),
    ("devops_project", ("devops", "docker", "kubernetes", "terraform", "cicd", "ci/cd")),
)

def _strip_code_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    return stripped


def _parse_model_json(text: str) -> dict[str, Any]:
    stripped = _strip_code_fences(text)
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end != -1 and start < end:
        stripped = stripped[start : end + 1]
    return json.loads(stripped)


def _build_prompt(user_prompt: str) -> str:
    freshness_seed = uuid4().hex
    return (
        "You are a general software project assistant. "
        "Suggest exactly 3 fresh, distinct, specific project ideas for the user's requested "
        "topic or technology: exactly 1 beginner, exactly 1 intermediate, and exactly 1 advanced. "
        "The topic can be anything: React, Node.js, mobile apps, AI, games, data, DevOps, "
        "business tools, automation, or another software domain. "
        "Do not use generic templates or repeated titles such as fundamentals project, CRUD starter, "
        "starter app, todo app, production-ready buildout, or advanced capstone. "
        "Do not reuse a generic beginner CRUD idea unless the user explicitly asks for CRUD, and even "
        "then make the product domain specific. "
        "Each idea must have a concrete product concept, target user, and technical angle. "
        "Return the ideas in this order: beginner, intermediate, advanced. "
        "Return JSON only with this shape: {\"suggestions\": "
        "[{\"category\": \"short_snake_case_topic\", "
        "\"difficulty_level\": \"beginner|intermediate|advanced\", "
        "\"title\": \"...\", \"rationale\": \"...\"}]}. "
        "No extra keys, no markdown. Keep each idea directly related to the user's topic. "
        f"Freshness seed: {freshness_seed}. "
        f"User request: {user_prompt}"
    )


def _openrouter_error_message(response: httpx.Response) -> str:
    try:
        payload = response.json()
        message = str(payload.get("error", {}).get("message") or "").strip()
    except Exception:
        message = response.text.strip()

    if response.status_code == 401:
        message = "Invalid OpenRouter API key"
    elif response.status_code == 429:
        message = "Free OpenRouter rate limit reached. Please wait and try again."
    elif not message:
        message = response.reason_phrase
    return f"OpenRouter API returned {response.status_code}: {message[:240]}"


def _is_provider_bad_request(response: httpx.Response) -> bool:
    if response.status_code != 400:
        return False
    try:
        payload = response.json()
        message = str(payload.get("error", {}).get("message") or "").lower()
    except Exception:
        message = response.text.lower()
    return "provider returned error" in message


def _extract_openrouter_content(response_json: dict[str, Any]) -> str:
    content = response_json["choices"][0]["message"]["content"]
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            str(part.get("text", ""))
            for part in content
            if isinstance(part, dict) and part.get("type") in {None, "text"}
        )
    return str(content)


def _openrouter_headers() -> dict[str, str]:
    settings = get_settings()
    if (
        not settings.openrouter_api_key
        or settings.openrouter_api_key == "your_openrouter_api_key_here"
    ):
        raise OpenRouterServiceError("OPENROUTER_API_KEY is not configured")

    return {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": settings.openrouter_site_url or "http://localhost:5173",
        "X-Title": settings.openrouter_app_title,
    }


def _request_openrouter(prompt: str, *, use_response_format: bool = True) -> dict[str, Any]:
    load_dotenv(BASE_DIR / ".env")
    load_dotenv(BASE_DIR / "backend" / ".env", override=True)
    settings = get_settings()
    payload = {
        "model": settings.openrouter_model,
        "messages": [
            {"role": "system", "content": OPENROUTER_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 2048,
    }
    if use_response_format:
        payload["response_format"] = {"type": "json_object"}

    last_error = "Failed to reach OpenRouter API"
    with httpx.Client(timeout=20.0) as client:
        for attempt in range(OPENROUTER_REQUEST_ATTEMPTS):
            try:
                response = client.post(
                    OPENROUTER_CHAT_COMPLETIONS_URL,
                    headers=_openrouter_headers(),
                    json=payload,
                )
            except httpx.TimeoutException as exc:
                last_error = "Timed out contacting OpenRouter API"
                if attempt < OPENROUTER_REQUEST_ATTEMPTS - 1:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                raise OpenRouterServiceError(last_error) from exc
            except httpx.RequestError as exc:
                last_error = "Network error contacting OpenRouter API"
                if attempt < OPENROUTER_REQUEST_ATTEMPTS - 1:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                raise OpenRouterServiceError(last_error) from exc

            if response.is_success:
                return response.json()

            provider_bad_request = _is_provider_bad_request(response)
            if use_response_format and provider_bad_request:
                return _request_openrouter(prompt, use_response_format=False)

            last_error = _openrouter_error_message(response)
            if (
                (provider_bad_request or response.status_code in RETRYABLE_OPENROUTER_STATUS_CODES)
                and attempt < OPENROUTER_REQUEST_ATTEMPTS - 1
            ):
                time.sleep(0.5 * (attempt + 1))
                continue
            raise OpenRouterServiceError(last_error, status_code=response.status_code)

    raise OpenRouterServiceError(last_error)


def _normalize_suggestions(raw: dict[str, Any]) -> list[dict[str, str]]:
    suggestions: list[dict[str, str]] = []
    for item in raw.get("suggestions", []):
        try:
            difficulty_level = DifficultyLevel(item["difficulty_level"])
        except Exception:
            continue

        title = str(item.get("title", "")).strip()
        rationale = str(item.get("rationale", "")).strip()
        if not title or not rationale:
            continue
        if any(pattern in title.lower() for pattern in GENERIC_TITLE_PATTERNS):
            continue
        category = _clean_category(
            str(item.get("category") or _select_category(f"{title} {rationale}"))
        )

        suggestions.append(
            {
                "category": category,
                "difficulty_level": difficulty_level.value,
                "title": title,
                "rationale": rationale,
            }
        )

    return suggestions


def _select_suggestion_set(suggestions: list[dict[str, str]]) -> list[dict[str, str]]:
    selected: list[dict[str, str]] = []
    used_titles: set[str] = set()

    for difficulty in SUGGESTION_DIFFICULTY_ORDER:
        match = next(
            (
                suggestion
                for suggestion in suggestions
                if suggestion["difficulty_level"] == difficulty
                and suggestion["title"].strip().lower() not in used_titles
            ),
            None,
        )
        if match is None:
            return []
        selected.append(match)
        used_titles.add(match["title"].strip().lower())

    return selected


def _clean_category(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return (normalized or "software_project")[:80]


def _select_category(user_prompt: str) -> str:
    prompt = user_prompt.lower()
    frontend_terms = ("react", "vue", "angular", "svelte", "frontend", "next.js", "nextjs")
    backend_terms = ("node", "express", "api", "backend", "django", "fastapi", "spring")
    if any(term in prompt for term in frontend_terms) and any(
        term in prompt for term in backend_terms
    ):
        return "full_stack_web_app"
    for category, keywords in CATEGORY_KEYWORDS:
        if any(keyword in prompt for keyword in keywords):
            return category
    return "software_project"


def _select_template_project_type(user_prompt: str) -> ProjectType | None:
    prompt = user_prompt.lower()
    for project_type, keywords in TEMPLATE_PROJECT_KEYWORDS:
        if any(keyword in prompt for keyword in keywords):
            return project_type
    return None


def _template_suggestion(
    project_type: ProjectType,
    difficulty_level: DifficultyLevel,
) -> dict[str, str]:
    template = load_template(project_type, difficulty_level)
    return {
        "category": project_type.value,
        "difficulty_level": difficulty_level.value,
        "title": template["idea"],
        "rationale": template["why_this_project_matters"],
    }


def _template_suggestions_from_library(user_prompt: str) -> list[dict[str, str]]:
    project_type = _select_template_project_type(user_prompt)
    if project_type is not None:
        choices = (
            (project_type, DifficultyLevel.beginner),
            (project_type, DifficultyLevel.intermediate),
            (project_type, DifficultyLevel.advanced),
        )
    else:
        choices = DEFAULT_TEMPLATE_SUGGESTIONS

    return [
        _template_suggestion(choice_project_type, choice_difficulty)
        for choice_project_type, choice_difficulty in choices
    ]


def _details_from_template(suggestion: dict[str, str]) -> dict[str, Any]:
    try:
        project_type = ProjectType(str(suggestion.get("category", "")))
        difficulty_level = DifficultyLevel(str(suggestion.get("difficulty_level", "")))
        template = load_template(project_type, difficulty_level)
    except (ValueError, TemplateNotFoundError):
        project_type = ProjectType.docker
        difficulty_level = DifficultyLevel.beginner
        template = load_template(project_type, difficulty_level)

    readme_outline = [
        line.strip("# ").strip()
        for line in template["readme"].splitlines()
        if line.startswith("#")
    ]
    code_paths = [code_file.path for code_file in template["code_files"]]

    return ProjectDetailsResponse.model_validate(
        {
            "title": template["idea"],
            "category": project_type.value,
            "difficulty_level": difficulty_level.value,
            "rationale": template["why_this_project_matters"],
            "overview": template["why_this_project_matters"],
            "architecture": [template["architecture"]],
            "recommended_tools": template["tools"],
            "implementation_steps": template["steps"],
            "deliverables": [
                "Template-backed project plan",
                "Source files: " + ", ".join(code_paths),
                "README outline: " + ", ".join(readme_outline or ["Overview", "Setup", "Usage"]),
                "Downloadable ZIP and PDF are available from the generator flow.",
            ],
            "risks": [
                "Adjust placeholder values before deploying to shared or cloud environments.",
                "Review secrets, credentials, and network exposure before production use.",
                "Validate commands locally before adding automation around the template.",
            ],
        }
    ).model_dump(mode="json")


def _is_template_manifest_suggestion(suggestion: dict[str, str]) -> bool:
    try:
        project_type = ProjectType(str(suggestion.get("category", "")))
        difficulty_level = DifficultyLevel(str(suggestion.get("difficulty_level", "")))
        template = load_template(project_type, difficulty_level)
    except (ValueError, TemplateNotFoundError):
        return False

    return str(suggestion.get("title", "")).strip() == str(template["idea"]).strip()


def _fallback_domain(user_prompt: str) -> str:
    prompt = user_prompt.lower()
    matches = (
        ("docker", ("docker", "container", "compose")),
        ("kubernetes", ("kubernetes", "k8s", "helm", "cluster")),
        ("cicd", ("ci/cd", "cicd", "pipeline", "github actions", "gitlab ci")),
        ("terraform", ("terraform", "iac", "infrastructure as code")),
        ("aws", ("aws", "ec2", "lambda", "ecs", "cloudwatch", "s3")),
        ("linux_automation", ("linux", "bash", "shell", "cron", "automation")),
        ("monitoring", ("monitoring", "observability", "prometheus", "grafana", "logs")),
        ("blockchain_project", ("blockchain", "web3", "smart contract", "crypto")),
        ("full_stack_web_app", ("full stack", "fullstack", "mern", "web app", "saas")),
        ("frontend_web_app", ("react", "vue", "angular", "svelte", "frontend")),
        ("backend_api", ("node", "express", "api", "backend", "django", "fastapi", "spring")),
        ("mobile_app", ("mobile", "android", "ios", "react native", "flutter")),
        ("ai_ml_project", ("artificial intelligence", "machine learning", "llm", "chatbot", "computer vision")),
        ("data_project", ("data", "analytics", "dashboard", "etl", "warehouse", "pipeline")),
        ("game_project", ("game", "unity", "godot", "phaser")),
        ("ecommerce_project", ("ecommerce", "e-commerce", "shop", "store", "marketplace")),
        ("cybersecurity_project", ("cyber", "security", "soc", "vulnerability", "pentest")),
    )
    for domain, keywords in matches:
        if any(keyword in prompt for keyword in keywords):
            return domain
    return _clean_category(user_prompt) or "software_project"


def _topic_label(user_prompt: str, domain: str) -> str:
    cleaned = re.sub(r"\s+", " ", user_prompt.strip())
    if cleaned:
        return cleaned[:80]
    return domain.replace("_", " ")


def _fallback_title_set(user_prompt: str, domain: str) -> dict[str, str]:
    configured = FALLBACK_TITLES.get(domain)
    if configured:
        return configured

    topic = _topic_label(user_prompt, domain).title()
    return {
        "beginner": f"Beginner {topic} Project: Focused Starter Build",
        "intermediate": f"Intermediate {topic} Project: Feature-Rich Product Build",
        "advanced": f"Advanced {topic} Project: Production-Ready Platform",
    }


FALLBACK_TITLES: dict[str, dict[str, str]] = {
    "docker": {
        "beginner": "Beginner Docker Project: Containerized Flask Service",
        "intermediate": "Intermediate Docker Project: Multi-Service App with Compose",
        "advanced": "Advanced Docker Project: Production Container Platform",
    },
    "kubernetes": {
        "beginner": "Beginner Kubernetes Project: Deploy a Web App",
        "intermediate": "Intermediate Kubernetes Project: Autoscaled API Stack",
        "advanced": "Advanced Kubernetes Project: Blue-Green Platform Rollout",
    },
    "cicd": {
        "beginner": "Beginner CI/CD Project: Test and Build Pipeline",
        "intermediate": "Intermediate CI/CD Project: Container Release Workflow",
        "advanced": "Advanced CI/CD Project: Progressive Delivery Pipeline",
    },
    "terraform": {
        "beginner": "Beginner Terraform Project: Reusable VM Module",
        "intermediate": "Intermediate Terraform Project: Networked App Infrastructure",
        "advanced": "Advanced Terraform Project: Multi-Environment IaC Platform",
    },
    "aws": {
        "beginner": "Beginner AWS Project: Static Site with Secure Storage",
        "intermediate": "Intermediate AWS Project: Containerized API on ECS",
        "advanced": "Advanced AWS Project: Event-Driven Deployment Platform",
    },
    "linux_automation": {
        "beginner": "Beginner Linux Automation Project: Server Bootstrap Script",
        "intermediate": "Intermediate Linux Automation Project: Scheduled Backup System",
        "advanced": "Advanced Linux Automation Project: Fleet Maintenance Toolkit",
    },
    "monitoring": {
        "beginner": "Beginner Monitoring Project: Host Metrics Dashboard",
        "intermediate": "Intermediate Monitoring Project: App Observability Stack",
        "advanced": "Advanced Monitoring Project: SLO and Alerting Platform",
    },
    "general_devops": {
        "beginner": "Beginner DevOps Project: Local App Delivery Workflow",
        "intermediate": "Intermediate DevOps Project: Container Pipeline and Deployment",
        "advanced": "Advanced DevOps Project: Production Delivery Platform",
    },
}


def _fallback_suggestions(user_prompt: str, note: str = FALLBACK_GENERAL_NOTE) -> list[dict[str, str]]:
    suggestions = catalog_suggestions_for_prompt(user_prompt)
    return [
        {
            **suggestion,
            "rationale": f"{note} {suggestion['rationale']}",
        }
        for suggestion in suggestions
    ]


def _fallback_details(
    user_prompt: str,
    suggestion: dict[str, str],
    note: str = FALLBACK_GENERAL_NOTE,
) -> dict[str, Any]:
    domain = catalog_clean_category(str(suggestion.get("category") or "")) or _fallback_domain(user_prompt)
    difficulty = str(suggestion.get("difficulty_level") or DifficultyLevel.beginner.value)
    if difficulty not in SUGGESTION_DIFFICULTY_ORDER:
        difficulty = DifficultyLevel.beginner.value
    titles = _fallback_title_set(user_prompt, domain)
    title = str(suggestion.get("title") or titles[difficulty])

    domain_tools = {
        "docker": ["Docker", "Docker Compose", "FastAPI", "Redis", "Make"],
        "kubernetes": ["kubectl", "Kubernetes", "Ingress Controller", "HPA", "Helm"],
        "cicd": ["GitHub Actions", "Docker", "pytest", "Trivy", "Deployment scripts"],
        "terraform": ["Terraform", "AWS provider", "Remote state", "tfvars", "tflint"],
        "aws": ["AWS IAM", "S3", "ECS or Lambda", "CloudWatch", "AWS CLI"],
        "linux_automation": ["Bash", "systemd", "cron", "rsync", "journalctl"],
        "monitoring": ["Prometheus", "Grafana", "Alertmanager", "Node Exporter", "Loki"],
        "general_devops": ["Git", "Docker", "CI/CD", "Monitoring", "README runbooks"],
        "react": ["React", "TypeScript", "Vite", "React Router", "Testing Library"],
        "next_js": ["Next.js", "TypeScript", "PostgreSQL", "Prisma", "Vercel"],
        "node_js": ["Node.js", "Express.js", "PostgreSQL", "Redis", "Vitest"],
        "express_js": ["Express.js", "Node.js", "JWT", "PostgreSQL", "Supertest"],
        "fastapi": ["FastAPI", "Pydantic", "SQLAlchemy", "PostgreSQL", "pytest"],
        "django": ["Django", "Django REST Framework", "PostgreSQL", "Celery", "pytest"],
        "python": ["Python", "FastAPI or Flask", "pytest", "PostgreSQL", "Docker"],
        "java": ["Java", "Spring Boot", "Maven or Gradle", "PostgreSQL", "JUnit"],
        "go": ["Go", "Gin or Chi", "PostgreSQL", "Docker", "go test"],
        "typescript": ["TypeScript", "Node.js", "ESLint", "Vitest", "Playwright"],
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
    fallback_tools = [
        "Git",
        "Relevant language runtime and package manager",
        "Database or storage layer when needed",
        "Test runner",
        "Docker or local development scripts",
        "README and architecture notes",
    ]
    rationale = str(suggestion.get("rationale") or "").strip()

    return ProjectDetailsResponse.model_validate(
        {
            "title": title,
            "category": domain,
            "difficulty_level": difficulty,
            "rationale": rationale or f"{note} The plan is scoped for a {difficulty} project.",
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
            "recommended_tools": domain_tools.get(domain, fallback_tools),
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
    ).model_dump(mode="json")


def _build_details_prompt(user_prompt: str, selection: dict[str, str]) -> str:
    return (
        "You are a senior software architect and project mentor. "
        "Return JSON only (no markdown) for the selected project idea. "
        "The project can be in any software domain or technology stack. "
        "Use a concise snake_case category that matches the project topic. "
        "JSON shape must be: {"
        "\"title\": str, "
        "\"category\": str, "
        "\"difficulty_level\": str, "
        "\"rationale\": str, "
        "\"overview\": str, "
        "\"architecture\": [str], "
        "\"recommended_tools\": [str], "
        "\"implementation_steps\": [str], "
        "\"deliverables\": [str], "
        "\"risks\": [str]"
        "}. "
        "Keep lists concise but actionable (5-10 items). "
        f"User request: {user_prompt} "
        f"Selected idea: {json.dumps(selection, ensure_ascii=False)}"
    )


def _normalize_details(raw: dict[str, Any], fallback: dict[str, str]) -> dict[str, Any]:
    title = str(raw.get("title") or fallback["title"]).strip()
    rationale = str(raw.get("rationale") or fallback.get("rationale", "")).strip()
    overview = str(raw.get("overview") or "").strip() or "High-level project plan and scope."
    category = _clean_category(str(fallback["category"] or raw.get("category")))

    try:
        difficulty_level = DifficultyLevel(
            str(raw.get("difficulty_level") or fallback["difficulty_level"])
        )
    except Exception:
        difficulty_level = DifficultyLevel(fallback["difficulty_level"])

    def as_list(value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return []

    architecture = as_list(raw.get("architecture"))
    recommended_tools = as_list(raw.get("recommended_tools"))
    implementation_steps = as_list(raw.get("implementation_steps"))
    deliverables = as_list(raw.get("deliverables"))
    risks = as_list(raw.get("risks"))

    if not architecture:
        architecture = ["Define components and service boundaries", "Map data flows and dependencies"]
    if not recommended_tools:
        recommended_tools = ["Git", "Package manager", "Test runner", "Database if needed"]
    if not implementation_steps:
        implementation_steps = [
            "Define requirements and success criteria",
            "Design architecture and choose tooling",
            "Implement and validate locally",
            "Add tests and quality checks",
            "Prepare deployment or sharing instructions",
        ]
    if not deliverables:
        deliverables = ["Architecture notes", "Source code", "README", "Demo or deployment guide"]
    if not risks:
        risks = ["Scope creep", "Unclear requirements", "Integration complexity"]

    details = {
        "title": title,
        "category": category,
        "difficulty_level": difficulty_level.value,
        "rationale": rationale or fallback.get("rationale", ""),
        "overview": overview,
        "architecture": architecture,
        "recommended_tools": recommended_tools,
        "implementation_steps": implementation_steps,
        "deliverables": deliverables,
        "risks": risks,
    }

    # Validate against the response schema for consistency.
    validated = ProjectDetailsResponse.model_validate(details)
    return validated.model_dump(mode="json")


def get_project_details(user_prompt: str, suggestion: dict[str, str]) -> dict[str, Any]:
    if _is_template_manifest_suggestion(suggestion):
        return _details_from_template(suggestion)

    return _fallback_details(user_prompt, suggestion, "Template catalog plan generated locally.")


def get_project_suggestions(user_prompt: str) -> list[dict[str, str]]:
    return catalog_suggestions_for_prompt(user_prompt)
