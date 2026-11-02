"""The MVP relational model; Alembic owns schema creation."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    MetaData,
    SmallInteger,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(table_name)s_%(column_0_name)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


class Timestamps:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Owner(Timestamps, Base):
    __tablename__ = "owners"
    __table_args__ = (
        CheckConstraint("id = 1", name="single_owner"),
        CheckConstraint("length(btrim(username)) > 0", name="username_not_blank"),
        CheckConstraint(
            "password_hash IS NULL OR length(btrim(password_hash)) > 0",
            name="password_hash_not_blank",
        ),
    )

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, default=1)
    username: Mapped[str] = mapped_column(Text, unique=True)
    password_hash: Mapped[str | None] = mapped_column(Text)
    failed_logins: Mapped[int] = mapped_column(default=0, server_default="0")
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class OwnerSession(Base):
    __tablename__ = "owner_sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[int] = mapped_column(ForeignKey("owners.id", ondelete="CASCADE"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class JobDefinition(Timestamps, Base):
    __tablename__ = "job_definitions"
    __table_args__ = (
        CheckConstraint("length(btrim(description)) > 0", name="description_not_blank"),
        CheckConstraint("state IN ('draft', 'ready')", name="valid_state"),
        CheckConstraint("control_version >= 0", name="valid_control_version"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("owners.id", ondelete="CASCADE"), unique=True
    )
    description: Mapped[str] = mapped_column(Text)
    state: Mapped[str] = mapped_column(Text, default="draft", server_default="draft")
    assessment: Mapped[dict[str, Any] | None] = mapped_column(JSONB(none_as_null=True))
    clarification_paused: Mapped[bool] = mapped_column(
        default=False, server_default="false"
    )
    control_version: Mapped[int] = mapped_column(default=0, server_default="0")


class Preference(Timestamps, Base):
    __tablename__ = "preferences"
    __table_args__ = (
        UniqueConstraint("definition_id", "key"),
        CheckConstraint("length(btrim(key)) > 0", name="key_not_blank"),
        CheckConstraint(
            "category IN ('role', 'seniority', 'responsibilities',"
            " 'technical_interests',"
            " 'company_context', 'compensation', 'location', 'work_arrangement',"
            " 'work_life_balance')",
            name="valid_category",
        ),
        CheckConstraint(
            "priority IN ('mandatory', 'preferred', 'excluded')", name="valid_priority"
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    definition_id: Mapped[UUID] = mapped_column(
        ForeignKey("job_definitions.id", ondelete="CASCADE"), index=True
    )
    key: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(Text)
    value: Mapped[Any | None] = mapped_column(JSONB(none_as_null=True))
    note: Mapped[str | None] = mapped_column(Text)


class Source(Timestamps, Base):
    __tablename__ = "sources"
    __table_args__ = (
        UniqueConstraint("definition_id", "file_slot"),
        CheckConstraint("kind IN ('file', 'url', 'text')", name="valid_kind"),
        CheckConstraint("length(btrim(display_name)) > 0", name="name_not_blank"),
        CheckConstraint(
            "(kind = 'file' AND file_slot BETWEEN 1 AND 5 AND file_slot IS NOT NULL"
            " AND object_key IS NOT NULL AND size_bytes BETWEEN 1 AND 10485760"
            " AND size_bytes IS NOT NULL AND url IS NULL AND media_type IN"
            " ('application/pdf', 'application/msword',"
            " 'application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document',"
            " 'text/markdown') AND media_type IS NOT NULL) OR"
            " (kind IN ('url', 'text') AND file_slot IS NULL AND object_key IS NULL"
            " AND size_bytes IS NULL AND media_type IS NULL)",
            name="file_metadata",
        ),
        CheckConstraint(
            "(kind = 'url' AND url IS NOT NULL AND url ~ '^https?://') OR"
            " (kind != 'url' AND url IS NULL)",
            name="url_metadata",
        ),
        CheckConstraint(
            "extraction_state IN ('pending', 'ready', 'failed')",
            name="valid_extraction_state",
        ),
        CheckConstraint(
            "extraction_state != 'ready' OR"
            " (extracted_text IS NOT NULL AND length(btrim(extracted_text)) > 0)",
            name="ready_has_text",
        ),
        CheckConstraint(
            "reviewed_at IS NULL OR extraction_state = 'ready'",
            name="review_requires_text",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    definition_id: Mapped[UUID] = mapped_column(
        ForeignKey("job_definitions.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(Text)
    display_name: Mapped[str] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(Text)
    object_key: Mapped[UUID | None] = mapped_column(unique=True)
    file_slot: Mapped[int | None] = mapped_column(SmallInteger)
    media_type: Mapped[str | None] = mapped_column(Text)
    size_bytes: Mapped[int | None]
    extraction_state: Mapped[str] = mapped_column(
        Text, default="pending", server_default="pending"
    )
    extracted_text: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    original_stored: Mapped[bool] = mapped_column(default=False, server_default="false")
    extraction_error: Mapped[dict | None] = mapped_column(JSONB(none_as_null=True))


class BackgroundFact(Timestamps, Base):
    __tablename__ = "background_facts"
    __table_args__ = (
        CheckConstraint("length(btrim(content)) > 0", name="content_not_blank"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    source_id: Mapped[UUID] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"), index=True
    )
    content: Mapped[str] = mapped_column(Text)


class Clarification(Timestamps, Base):
    __tablename__ = "clarifications"
    __table_args__ = (
        UniqueConstraint("definition_id", "round_id", "position"),
        CheckConstraint("position BETWEEN 1 AND 3", name="round_position"),
        CheckConstraint("length(btrim(question)) > 0", name="question_not_blank"),
        CheckConstraint(
            "answer_state IN ('unanswered', 'answered', 'skipped', 'unknown')",
            name="valid_answer_state",
        ),
        CheckConstraint(
            "(answer_state = 'answered' AND answer IS NOT NULL"
            " AND length(btrim(answer)) > 0) OR"
            " (answer_state != 'answered' AND answer IS NULL)",
            name="answer_matches_state",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    definition_id: Mapped[UUID] = mapped_column(
        ForeignKey("job_definitions.id", ondelete="CASCADE"), index=True
    )
    round_id: Mapped[UUID]
    position: Mapped[int] = mapped_column(SmallInteger)
    question: Mapped[str] = mapped_column(Text)
    answer_state: Mapped[str] = mapped_column(
        Text, default="unanswered", server_default="unanswered"
    )
    answer: Mapped[str | None] = mapped_column(Text)


class DocumentDeletion(Base):
    __tablename__ = "document_deletions"

    object_key: Mapped[UUID] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
