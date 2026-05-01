import json
import random
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from backend.utils.config import get_settings
from backend.utils.schemas import DifficultyLevel

CATALOG_RELATIVE_PATH = Path("project_ideas") / "catalog.json"
SUGGESTION_DIFFICULTIES = (
    DifficultyLevel.beginner.value,
    DifficultyLevel.intermediate.value,
    DifficultyLevel.advanced.value,
)
FULL_CATALOG_PATTERNS = (
    "50",
    "all ideas",
    "all project ideas",
    "every idea",
    "full catalog",
    "complete catalog",
)
RECENT_TITLE_LIMIT = 15
_RECENT_TITLES_BY_TOPIC: dict[str, list[str]] = {}


class ProjectIdeaCatalogError(RuntimeError):
    pass


def clean_category(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return (normalized or "software_project")[:80]


def _catalog_path() -> Path:
    return get_settings().templates_directory / CATALOG_RELATIVE_PATH


@lru_cache
def _load_catalog() -> dict[str, Any]:
    path = _catalog_path()
    if not path.exists():
        raise ProjectIdeaCatalogError(f"Project idea catalog missing: {path}")

    catalog = json.loads(path.read_text(encoding="utf-8"))
    topics = catalog.get("topics")
    blueprints = catalog.get("idea_blueprints")
    if not isinstance(topics, list) or not isinstance(blueprints, list):
        raise ProjectIdeaCatalogError("Project idea catalog must define topics and idea_blueprints")
    if len(blueprints) != 50:
        raise ProjectIdeaCatalogError("Project idea catalog must contain exactly 50 idea blueprints")

    return catalog


def _normalize_phrase(value: str) -> str:
    normalized = value.lower().replace("&", " and ")
    normalized = re.sub(r"[^a-z0-9+#.]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def _phrase_in_prompt(prompt: str, phrase: str) -> bool:
    prompt = f" {_normalize_phrase(prompt)} "
    phrase = _normalize_phrase(phrase)
    if not phrase:
        return False
    return f" {phrase} " in prompt


def _topic_aliases(topic: str, catalog: dict[str, Any]) -> list[str]:
    aliases = [topic]
    configured_aliases = catalog.get("aliases", {}).get(topic, [])
    if isinstance(configured_aliases, list):
        aliases.extend(str(alias) for alias in configured_aliases)
    aliases.append(clean_category(topic).replace("_", " "))
    return sorted(set(aliases), key=len, reverse=True)


def select_topic(user_prompt: str) -> str:
    catalog = _load_catalog()
    prompt = user_prompt.strip()
    if not prompt:
        return "Software Project"

    scored_topics: list[tuple[int, str]] = []
    for topic in catalog["topics"]:
        aliases = _topic_aliases(str(topic), catalog)
        if any(_phrase_in_prompt(prompt, alias) for alias in aliases):
            scored_topics.append((max(len(alias) for alias in aliases), str(topic)))

    if scored_topics:
        return sorted(scored_topics, reverse=True)[0][1]

    cleaned = re.sub(r"\s+", " ", prompt).strip()
    return cleaned[:80].title() if cleaned else "Software Project"


def wants_full_catalog(user_prompt: str) -> bool:
    prompt = user_prompt.lower()
    return any(pattern in prompt for pattern in FULL_CATALOG_PATTERNS)


def ideas_for_topic(topic: str) -> list[dict[str, str]]:
    catalog = _load_catalog()
    category = clean_category(topic)
    ideas: list[dict[str, str]] = []

    for blueprint in catalog["idea_blueprints"]:
        difficulty = str(blueprint.get("difficulty_level", "")).strip().lower()
        if difficulty not in SUGGESTION_DIFFICULTIES:
            raise ProjectIdeaCatalogError(f"Invalid difficulty in project idea catalog: {difficulty}")

        ideas.append(
            {
                "category": category,
                "difficulty_level": difficulty,
                "title": str(blueprint["title"]).format(topic=topic),
                "rationale": str(blueprint["rationale"]).format(topic=topic),
            }
        )

    return ideas


def suggestions_for_prompt(user_prompt: str) -> list[dict[str, str]]:
    topic = select_topic(user_prompt)
    ideas = ideas_for_topic(topic)
    random.shuffle(ideas)

    if wants_full_catalog(user_prompt):
        return ideas

    recent_titles = set(_RECENT_TITLES_BY_TOPIC.get(topic, []))
    selected: list[dict[str, str]] = []
    for difficulty in SUGGESTION_DIFFICULTIES:
        matches = [idea for idea in ideas if idea["difficulty_level"] == difficulty]
        fresh_matches = [idea for idea in matches if idea["title"] not in recent_titles]
        selected.append(random.choice(fresh_matches or matches))

    _RECENT_TITLES_BY_TOPIC[topic] = (
        [idea["title"] for idea in selected] + _RECENT_TITLES_BY_TOPIC.get(topic, [])
    )[:RECENT_TITLE_LIMIT]
    random.shuffle(selected)
    return selected
