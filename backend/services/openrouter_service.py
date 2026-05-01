import json
import re
import time
from typing import Any
from uuid import uuid4

import httpx

from backend.utils.config import get_settings
from backend.utils.schemas import DifficultyLevel, ProjectDetailsResponse

SUGGESTION_COUNT = 5
MAX_AI_ATTEMPTS = 3
OPENROUTER_REQUEST_ATTEMPTS = 2
OPENROUTER_CHAT_COMPLETIONS_URL = "https://openrouter.ai/api/v1/chat/completions"
RETRYABLE_OPENROUTER_STATUS_CODES = {429, 500, 502, 503, 504}
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


class OpenRouterServiceError(RuntimeError):
    pass


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
        "Suggest exactly 5 fresh, distinct, specific project ideas for the user's requested "
        "topic or technology. "
        "The topic can be anything: React, Node.js, mobile apps, AI, games, data, DevOps, "
        "business tools, automation, or another software domain. "
        "Do not use generic templates or repeated titles such as fundamentals project, CRUD starter, "
        "starter app, todo app, production-ready buildout, or advanced capstone. "
        "Do not reuse a generic beginner CRUD idea unless the user explicitly asks for CRUD, and even "
        "then make the product domain specific. "
        "Each idea must have a concrete product concept, target user, and technical angle. "
        "Use a mixed difficulty distribution such as 2 beginner, 1 intermediate, "
        "and 2 advanced ideas, or 1 beginner, 2 intermediate, and 2 advanced ideas. "
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

    if not message:
        message = response.reason_phrase
    return f"OpenRouter API returned {response.status_code}: {message[:240]}"


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
    if not settings.openrouter_api_key:
        raise OpenRouterServiceError("OPENROUTER_API_KEY is not configured")

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "X-OpenRouter-Title": settings.openrouter_app_title,
    }
    if settings.openrouter_site_url:
        headers["HTTP-Referer"] = settings.openrouter_site_url
    return headers


def _request_openrouter(prompt: str) -> dict[str, Any]:
    settings = get_settings()
    payload = {
        "model": settings.openrouter_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "top_p": 0.95,
        "max_tokens": 2048,
        "response_format": {"type": "json_object"},
    }

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

            last_error = _openrouter_error_message(response)
            if (
                response.status_code in RETRYABLE_OPENROUTER_STATUS_CODES
                and attempt < OPENROUTER_REQUEST_ATTEMPTS - 1
            ):
                time.sleep(0.5 * (attempt + 1))
                continue
            raise OpenRouterServiceError(last_error)

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
    category = _clean_category(str(raw.get("category") or fallback["category"]))

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
    prompt = _build_details_prompt(user_prompt, suggestion)
    fallback = {
        "title": str(suggestion.get("title", "Software project")),
        "category": _clean_category(str(suggestion.get("category") or _select_category(user_prompt))),
        "difficulty_level": str(suggestion.get("difficulty_level", DifficultyLevel.beginner.value)),
        "rationale": str(suggestion.get("rationale", "Aligned to your request.")),
    }

    try:
        response = _request_openrouter(prompt)
        raw_details = _parse_model_json(_extract_openrouter_content(response))
    except OpenRouterServiceError:
        raise
    except Exception:
        raise OpenRouterServiceError("OpenRouter returned invalid project details. Try again.")

    return _normalize_details(raw_details, fallback)


def get_project_suggestions(user_prompt: str) -> list[dict[str, str]]:
    last_failure = "OpenRouter returned too few project suggestions. Try again."
    for _ in range(MAX_AI_ATTEMPTS):
        prompt = _build_prompt(user_prompt)

        try:
            response = _request_openrouter(prompt)
            parsed = _parse_model_json(_extract_openrouter_content(response))
            suggestions = _normalize_suggestions(parsed)
        except OpenRouterServiceError:
            raise
        except Exception:
            last_failure = "OpenRouter returned invalid project suggestions. Try again."
            continue

        if len(suggestions) >= SUGGESTION_COUNT:
            return suggestions[:SUGGESTION_COUNT]

    raise OpenRouterServiceError(last_failure)
