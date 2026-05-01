import json
from pathlib import Path

from backend.utils.config import get_settings
from backend.utils.schemas import CodeFile, DifficultyLevel, ProjectType

settings = get_settings()

LANGUAGE_BY_EXTENSION = {
    ".md": "markdown",
    ".py": "python",
    ".tf": "hcl",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".json": "json",
    ".sh": "bash",
    ".txt": "text",
}


class TemplateNotFoundError(FileNotFoundError):
    pass


def _guess_language(path: Path) -> str:
    if path.name == "Dockerfile":
        return "dockerfile"
    return LANGUAGE_BY_EXTENSION.get(path.suffix.lower(), "text")


def _resolve_template_dir(project_type: ProjectType, difficulty_level: DifficultyLevel) -> Path:
    template_root = settings.templates_directory.resolve()
    template_dir = (template_root / project_type.value / difficulty_level.value).resolve()

    if template_root not in template_dir.parents:
        raise TemplateNotFoundError("Invalid template path requested")
    if not template_dir.exists():
        raise TemplateNotFoundError("Requested template does not exist")
    return template_dir


def _safe_template_file(template_dir: Path, file_path: Path) -> Path:
    if file_path.is_symlink() or not file_path.is_file():
        raise TemplateNotFoundError("Template contains an invalid file reference")

    resolved_file = file_path.resolve()
    if template_dir not in resolved_file.parents:
        raise TemplateNotFoundError("Template file escapes the template directory")

    return resolved_file


def load_template(project_type: ProjectType, difficulty_level: DifficultyLevel) -> dict:
    template_dir = _resolve_template_dir(project_type, difficulty_level)
    manifest_path = template_dir / "template.json"
    readme_path = template_dir / "README.md"

    if not manifest_path.exists() or not readme_path.exists():
        raise TemplateNotFoundError("Template metadata is incomplete")

    manifest = json.loads(
        _safe_template_file(template_dir, manifest_path).read_text(encoding="utf-8")
    )
    code_files: list[CodeFile] = []

    for file_path in sorted(template_dir.rglob("*")):
        if file_path.is_symlink() or not file_path.is_file():
            continue

        resolved_file = file_path.resolve()
        if template_dir not in resolved_file.parents:
            raise TemplateNotFoundError("Template file escapes the template directory")

        relative_path = file_path.relative_to(template_dir).as_posix()
        if relative_path in {"template.json", "README.md"}:
            continue

        code_files.append(
            CodeFile(
                path=relative_path,
                language=_guess_language(file_path),
                content=resolved_file.read_text(encoding="utf-8"),
            )
        )

    return {
        "idea": manifest["idea"],
        "why_this_project_matters": manifest["why_this_project_matters"],
        "architecture": manifest["architecture"],
        "tools": manifest["tools"],
        "steps": manifest["steps"],
        "code_files": code_files,
        "readme": _safe_template_file(template_dir, readme_path).read_text(
            encoding="utf-8"
        ),
    }
