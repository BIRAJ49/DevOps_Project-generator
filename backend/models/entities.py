from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    usage_records: Mapped[list["UsageRecord"]] = relationship(back_populates="user")
    generation_artifacts: Mapped[list["GenerationArtifact"]] = relationship(
        back_populates="user"
    )


class UsageRecord(Base):
    __tablename__ = "usage_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    ip_address: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    request_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_request_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    user: Mapped[User | None] = relationship(back_populates="usage_records")


class GenerationArtifact(Base):
    __tablename__ = "generation_artifacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    generation_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    ip_address: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    project_type: Mapped[str] = mapped_column(String(32), nullable=False)
    difficulty_level: Mapped[str] = mapped_column(String(32), nullable=False)
    storage_backend: Mapped[str] = mapped_column(String(16), nullable=False)
    zip_storage_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    zip_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    pdf_storage_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    pdf_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    user: Mapped[User | None] = relationship(back_populates="generation_artifacts")
