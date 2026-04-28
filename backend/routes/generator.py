from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user_optional
from backend.models.database import get_db
from backend.models.entities import GenerationArtifact, User
from backend.services.archive_service import (
    build_download_response,
    create_generation_artifacts,
    delete_stored_artifacts,
)
from backend.services.template_service import TemplateNotFoundError, load_template
from backend.services.usage_service import (
    GUEST_LIMIT_MESSAGE,
    get_guest_requests_used,
    get_remaining_guest_requests,
    record_usage,
)
from backend.utils.config import get_settings
from backend.utils.rate_limiter import rate_limit
from backend.utils.request import extract_client_ip
from backend.utils.schemas import ArtifactFormat, GenerateRequest, GenerateResponse

router = APIRouter(tags=["generator"])
settings = get_settings()
generate_rate_limit = rate_limit(
    "generate", settings.rate_limit_max_requests, settings.rate_limit_window_seconds
)


@router.post(
    "/generate",
    response_model=GenerateResponse,
    dependencies=[Depends(generate_rate_limit)],
)
def generate_project(
    payload: GenerateRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
) -> GenerateResponse:
    client_ip = extract_client_ip(request)

    if user is None:
        guest_requests_used = get_guest_requests_used(db, client_ip)
        if guest_requests_used >= settings.guest_project_limit:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=GUEST_LIMIT_MESSAGE)

    try:
        generated_project = load_template(payload.project_type, payload.difficulty_level)
    except TemplateNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    generation_id = uuid4().hex
    owner_reference = f"user-{user.id}" if user is not None else f"guest-{client_ip}"
    stored_artifacts = create_generation_artifacts(
        generation_id=generation_id,
        project_type=payload.project_type.value,
        difficulty_level=payload.difficulty_level.value,
        generated_project=generated_project,
        owner_reference=owner_reference,
    )

    artifact_record = GenerationArtifact(
        generation_id=generation_id,
        user_id=user.id if user is not None else None,
        ip_address=client_ip,
        project_type=payload.project_type.value,
        difficulty_level=payload.difficulty_level.value,
        storage_backend=settings.artifact_storage_backend,
        zip_storage_key=stored_artifacts.zip_artifact.storage_key,
        zip_filename=stored_artifacts.zip_artifact.filename,
        pdf_storage_key=stored_artifacts.pdf_artifact.storage_key,
        pdf_filename=stored_artifacts.pdf_artifact.filename,
    )

    try:
        db.add(artifact_record)
        db.commit()
        db.refresh(artifact_record)
    except Exception as exc:
        db.rollback()
        delete_stored_artifacts(stored_artifacts)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to persist generated artifact metadata",
        ) from exc

    usage_record = record_usage(db, user=user, ip_address=client_ip)
    guest_requests_remaining = (
        None
        if user is not None
        else get_remaining_guest_requests(usage_record.request_count, settings.guest_project_limit)
    )

    return GenerateResponse(
        generation_id=generation_id,
        project_type=payload.project_type,
        difficulty_level=payload.difficulty_level,
        idea=generated_project["idea"],
        why_this_project_matters=generated_project["why_this_project_matters"],
        architecture=generated_project["architecture"],
        tools=generated_project["tools"],
        steps=generated_project["steps"],
        code_files=generated_project["code_files"],
        readme=generated_project["readme"],
        download_url=f"{settings.api_prefix}/generate/{generation_id}/download/zip",
        download_zip_url=f"{settings.api_prefix}/generate/{generation_id}/download/zip",
        download_pdf_url=f"{settings.api_prefix}/generate/{generation_id}/download/pdf",
        is_authenticated=user is not None,
        guest_requests_remaining=guest_requests_remaining,
    )


@router.get("/generate/{generation_id}/download/{artifact_format}")
def download_generated_project(
    generation_id: str,
    artifact_format: ArtifactFormat,
    db: Session = Depends(get_db),
):
    artifact = db.scalar(
        select(GenerationArtifact).where(GenerationArtifact.generation_id == generation_id)
    )
    if artifact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Download not found")

    if artifact_format == ArtifactFormat.zip:
        return build_download_response(
            artifact_format=ArtifactFormat.zip,
            storage_key=artifact.zip_storage_key,
            filename=artifact.zip_filename,
            storage_backend=artifact.storage_backend,
        )

    return build_download_response(
        artifact_format=ArtifactFormat.pdf,
        storage_key=artifact.pdf_storage_key,
        filename=artifact.pdf_filename,
        storage_backend=artifact.storage_backend,
    )
