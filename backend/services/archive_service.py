from dataclasses import dataclass
from html import escape
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import boto3
from botocore.client import Config as BotoConfig
from fastapi import HTTPException, status
from fastapi.responses import FileResponse, RedirectResponse, Response
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Preformatted, SimpleDocTemplate, Spacer

from backend.utils.config import get_settings
from backend.utils.schemas import ArtifactFormat

settings = get_settings()


@dataclass(frozen=True)
class ArtifactPayload:
    artifact_format: ArtifactFormat
    filename: str
    content_type: str
    body: bytes


@dataclass(frozen=True)
class StoredArtifact:
    artifact_format: ArtifactFormat
    storage_key: str
    filename: str
    content_type: str


@dataclass(frozen=True)
class StoredArtifactSet:
    zip_artifact: StoredArtifact
    pdf_artifact: StoredArtifact


def _sanitize_segment(value: str) -> str:
    return "".join(character if character.isalnum() else "-" for character in value).strip("-")


def _bundle_name(project_type: str, difficulty_level: str, generation_id: str) -> str:
    return f"{project_type}-{difficulty_level}-{generation_id[:8]}"


def _bundle_root(project_type: str, difficulty_level: str) -> str:
    return f"{project_type}-{difficulty_level}-starter"


def build_generation_zip(
    generation_id: str,
    project_type: str,
    difficulty_level: str,
    generated_project: dict,
) -> ArtifactPayload:
    bundle_root = _bundle_root(project_type, difficulty_level)
    archive_buffer = BytesIO()

    with ZipFile(archive_buffer, "w", compression=ZIP_DEFLATED) as archive:
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
                    "",
                    "## Tools required",
                    *[f"- {tool}" for tool in generated_project["tools"]],
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

    return ArtifactPayload(
        artifact_format=ArtifactFormat.zip,
        filename=f"{_bundle_name(project_type, difficulty_level, generation_id)}.zip",
        content_type="application/zip",
        body=archive_buffer.getvalue(),
    )


def build_generation_pdf(
    generation_id: str,
    project_type: str,
    difficulty_level: str,
    generated_project: dict,
) -> ArtifactPayload:
    pdf_buffer = BytesIO()
    document = SimpleDocTemplate(
        pdf_buffer,
        pagesize=A4,
        title=generated_project["idea"],
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    heading_style = styles["Heading2"]
    body_style = styles["BodyText"]
    code_style = ParagraphStyle(
        "ArtifactCode",
        parent=styles["Code"],
        fontName="Courier",
        fontSize=8,
        leading=10,
        backColor=colors.whitesmoke,
        borderPadding=6,
    )

    story = [
        Paragraph(escape(generated_project["idea"]), title_style),
        Spacer(1, 0.2 * inch),
        Paragraph(
            escape(
                f"Project type: {project_type} | Difficulty: {difficulty_level} | Generation: {generation_id}"
            ),
            body_style,
        ),
        Spacer(1, 0.25 * inch),
    ]

    sections = [
        ("Why This Project Matters", generated_project["why_this_project_matters"]),
        ("Architecture", generated_project["architecture"]),
        ("Tools Required", "<br/>".join(f"- {escape(tool)}" for tool in generated_project["tools"])),
        (
            "Implementation Steps",
            "<br/>".join(
                f"{index}. {escape(step)}"
                for index, step in enumerate(generated_project["steps"], start=1)
            ),
        ),
        (
            "Starter Files Included",
            "<br/>".join(escape(code_file.path) for code_file in generated_project["code_files"]),
        ),
    ]

    for title, content in sections:
        story.append(Paragraph(title, heading_style))
        story.append(Spacer(1, 0.08 * inch))
        story.append(Paragraph(content, body_style))
        story.append(Spacer(1, 0.18 * inch))

    story.append(Paragraph("README Snapshot", heading_style))
    story.append(Spacer(1, 0.08 * inch))
    story.append(Preformatted(generated_project["readme"], code_style))

    document.build(story)
    return ArtifactPayload(
        artifact_format=ArtifactFormat.pdf,
        filename=f"{_bundle_name(project_type, difficulty_level, generation_id)}.pdf",
        content_type="application/pdf",
        body=pdf_buffer.getvalue(),
    )


def _artifact_storage_prefix(owner_segment: str, generation_id: str) -> str:
    prefix = settings.s3_artifact_prefix.strip("/ ")
    if prefix:
        return f"{prefix}/{owner_segment}/{generation_id}"
    return f"{owner_segment}/{generation_id}"


def _local_storage_root() -> Path:
    settings.archive_directory.mkdir(parents=True, exist_ok=True)
    return settings.archive_directory


def _s3_client():
    return boto3.client(
        "s3",
        region_name=settings.aws_region,
        endpoint_url=settings.s3_endpoint_url,
        config=BotoConfig(signature_version="s3v4"),
    )


def create_generation_artifacts(
    generation_id: str,
    project_type: str,
    difficulty_level: str,
    generated_project: dict,
    owner_reference: str,
) -> StoredArtifactSet:
    owner_segment = _sanitize_segment(owner_reference) or "anonymous"
    storage_prefix = _artifact_storage_prefix(owner_segment, generation_id)
    payloads = [
        build_generation_zip(generation_id, project_type, difficulty_level, generated_project),
        build_generation_pdf(generation_id, project_type, difficulty_level, generated_project),
    ]

    if settings.artifact_storage_backend == "s3":
        return _store_artifacts_in_s3(storage_prefix, payloads)
    return _store_artifacts_locally(storage_prefix, payloads)


def _store_artifacts_locally(
    storage_prefix: str,
    payloads: list[ArtifactPayload],
) -> StoredArtifactSet:
    root = _local_storage_root()
    stored_artifacts: dict[ArtifactFormat, StoredArtifact] = {}

    for payload in payloads:
        storage_key = f"{storage_prefix}/{payload.filename}"
        artifact_path = root / Path(storage_key)
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_bytes(payload.body)
        stored_artifacts[payload.artifact_format] = StoredArtifact(
            artifact_format=payload.artifact_format,
            storage_key=storage_key,
            filename=payload.filename,
            content_type=payload.content_type,
        )

    return StoredArtifactSet(
        zip_artifact=stored_artifacts[ArtifactFormat.zip],
        pdf_artifact=stored_artifacts[ArtifactFormat.pdf],
    )


def _store_artifacts_in_s3(
    storage_prefix: str,
    payloads: list[ArtifactPayload],
) -> StoredArtifactSet:
    client = _s3_client()
    stored_artifacts: dict[ArtifactFormat, StoredArtifact] = {}

    for payload in payloads:
        storage_key = f"{storage_prefix}/{payload.filename}"
        client.put_object(
            Bucket=settings.s3_bucket_name,
            Key=storage_key,
            Body=payload.body,
            ContentType=payload.content_type,
            ContentDisposition=f'attachment; filename="{payload.filename}"',
        )
        stored_artifacts[payload.artifact_format] = StoredArtifact(
            artifact_format=payload.artifact_format,
            storage_key=storage_key,
            filename=payload.filename,
            content_type=payload.content_type,
        )

    return StoredArtifactSet(
        zip_artifact=stored_artifacts[ArtifactFormat.zip],
        pdf_artifact=stored_artifacts[ArtifactFormat.pdf],
    )


def delete_stored_artifacts(artifacts: StoredArtifactSet) -> None:
    if settings.artifact_storage_backend == "s3":
        client = _s3_client()
        for artifact in (artifacts.zip_artifact, artifacts.pdf_artifact):
            client.delete_object(Bucket=settings.s3_bucket_name, Key=artifact.storage_key)
        return

    for artifact in (artifacts.zip_artifact, artifacts.pdf_artifact):
        artifact_path = _local_storage_root() / Path(artifact.storage_key)
        artifact_path.unlink(missing_ok=True)


def build_download_response(
    artifact_format: ArtifactFormat,
    storage_key: str,
    filename: str,
    storage_backend: str,
) -> Response:
    content_type = "application/zip" if artifact_format == ArtifactFormat.zip else "application/pdf"

    if storage_backend == "s3":
        url = _s3_client().generate_presigned_url(
            "get_object",
            Params={
                "Bucket": settings.s3_bucket_name,
                "Key": storage_key,
                "ResponseContentType": content_type,
                "ResponseContentDisposition": f'attachment; filename="{filename}"',
            },
            ExpiresIn=settings.artifact_download_ttl_seconds,
        )
        return RedirectResponse(url=url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    artifact_path = _local_storage_root() / Path(storage_key)
    if not artifact_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Download not found")

    return FileResponse(artifact_path, media_type=content_type, filename=filename)
