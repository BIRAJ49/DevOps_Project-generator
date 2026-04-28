from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from backend.utils.config import get_settings

settings = get_settings()


def create_generation_archive(
    generation_id: str,
    project_type: str,
    difficulty_level: str,
    generated_project: dict,
) -> Path:
    settings.archive_directory.mkdir(parents=True, exist_ok=True)
    archive_path = settings.archive_directory / f"{generation_id}.zip"
    bundle_root = f"{project_type}-{difficulty_level}-starter"

    with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr(f"{bundle_root}/README.md", generated_project["readme"])
        archive.writestr(
            f"{bundle_root}/docs/ARCHITECTURE.md",
            "\n".join(
                [
                    f"# {generated_project['idea']}",
                    "",
                    "## Why this project matters",
                    generated_project["why_this_project_matters"],
                    "",
                    "## Architecture",
                    generated_project["architecture"],
                ]
            ),
        )
        archive.writestr(
            f"{bundle_root}/docs/IMPLEMENTATION_GUIDE.md",
            "\n".join(
                ["# Implementation Guide", ""]
                + [f"{index}. {step}" for index, step in enumerate(generated_project["steps"], start=1)]
            ),
        )

        for code_file in generated_project["code_files"]:
            archive.writestr(f"{bundle_root}/{code_file.path}", code_file.content)

    return archive_path


def resolve_archive_path(generation_id: str) -> Path | None:
    archive_path = settings.archive_directory / f"{generation_id}.zip"
    if archive_path.exists():
        return archive_path
    return None

