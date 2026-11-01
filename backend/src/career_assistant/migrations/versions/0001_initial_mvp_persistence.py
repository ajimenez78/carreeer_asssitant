"""Initial MVP persistence

Revision ID: 0001
Revises:
"""

# ruff: noqa: E501
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "owners",
        sa.Column("id", sa.SmallInteger(), nullable=False),
        sa.Column("username", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("id = 1", name=op.f("ck_owners_single_owner")),
        sa.CheckConstraint(
            "length(btrim(username)) > 0", name=op.f("ck_owners_username_not_blank")
        ),
        sa.CheckConstraint(
            "password_hash IS NULL OR length(btrim(password_hash)) > 0",
            name=op.f("ck_owners_password_hash_not_blank"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_owners")),
        sa.UniqueConstraint("username", name=op.f("uq_owners_username")),
    )
    op.create_table(
        "job_definitions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.SmallInteger(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("state", sa.Text(), server_default="draft", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "state IN ('draft', 'ready')", name=op.f("ck_job_definitions_valid_state")
        ),
        sa.CheckConstraint(
            "length(btrim(description)) > 0",
            name=op.f("ck_job_definitions_description_not_blank"),
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["owners.id"],
            name=op.f("fk_job_definitions_owner_id_owners"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_job_definitions")),
        sa.UniqueConstraint("owner_id", name=op.f("uq_job_definitions_owner_id")),
    )
    op.create_table(
        "clarifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("definition_id", sa.Uuid(), nullable=False),
        sa.Column("round_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.SmallInteger(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column(
            "answer_state", sa.Text(), server_default="unanswered", nullable=False
        ),
        sa.Column("answer", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "(answer_state = 'answered' AND answer IS NOT NULL AND length(btrim(answer)) > 0) OR (answer_state != 'answered' AND answer IS NULL)",
            name=op.f("ck_clarifications_answer_matches_state"),
        ),
        sa.CheckConstraint(
            "answer_state IN ('unanswered', 'answered', 'skipped', 'unknown')",
            name=op.f("ck_clarifications_valid_answer_state"),
        ),
        sa.CheckConstraint(
            "length(btrim(question)) > 0",
            name=op.f("ck_clarifications_question_not_blank"),
        ),
        sa.CheckConstraint(
            "position BETWEEN 1 AND 3", name=op.f("ck_clarifications_round_position")
        ),
        sa.ForeignKeyConstraint(
            ["definition_id"],
            ["job_definitions.id"],
            name=op.f("fk_clarifications_definition_id_job_definitions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_clarifications")),
        sa.UniqueConstraint(
            "definition_id",
            "round_id",
            "position",
            name=op.f("uq_clarifications_definition_id"),
        ),
    )
    op.create_index(
        op.f("ix_clarifications_definition_id"),
        "clarifications",
        ["definition_id"],
        unique=False,
    )
    op.create_table(
        "preferences",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("definition_id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.Text(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("priority", sa.Text(), nullable=False),
        sa.Column(
            "value",
            postgresql.JSONB(none_as_null=True, astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "category IN ('role', 'seniority', 'responsibilities', 'technical_interests', 'company_context', 'compensation', 'location', 'work_arrangement', 'work_life_balance')",
            name=op.f("ck_preferences_valid_category"),
        ),
        sa.CheckConstraint(
            "priority IN ('mandatory', 'preferred', 'excluded')",
            name=op.f("ck_preferences_valid_priority"),
        ),
        sa.CheckConstraint(
            "length(btrim(key)) > 0", name=op.f("ck_preferences_key_not_blank")
        ),
        sa.ForeignKeyConstraint(
            ["definition_id"],
            ["job_definitions.id"],
            name=op.f("fk_preferences_definition_id_job_definitions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_preferences")),
        sa.UniqueConstraint(
            "definition_id", "key", name=op.f("uq_preferences_definition_id")
        ),
    )
    op.create_index(
        op.f("ix_preferences_definition_id"),
        "preferences",
        ["definition_id"],
        unique=False,
    )
    op.create_table(
        "sources",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("definition_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("object_key", sa.Uuid(), nullable=True),
        sa.Column("file_slot", sa.SmallInteger(), nullable=True),
        sa.Column("media_type", sa.Text(), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column(
            "extraction_state", sa.Text(), server_default="pending", nullable=False
        ),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "(kind = 'file' AND file_slot BETWEEN 1 AND 5 AND file_slot IS NOT NULL AND object_key IS NOT NULL AND size_bytes BETWEEN 1 AND 10485760 AND size_bytes IS NOT NULL AND url IS NULL AND media_type IN ('application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/markdown') AND media_type IS NOT NULL) OR (kind IN ('url', 'text') AND file_slot IS NULL AND object_key IS NULL AND size_bytes IS NULL AND media_type IS NULL)",
            name=op.f("ck_sources_file_metadata"),
        ),
        sa.CheckConstraint(
            "(kind = 'url' AND url IS NOT NULL AND url ~ '^https?://') OR (kind != 'url' AND url IS NULL)",
            name=op.f("ck_sources_url_metadata"),
        ),
        sa.CheckConstraint(
            "extraction_state != 'ready' OR (extracted_text IS NOT NULL AND length(btrim(extracted_text)) > 0)",
            name=op.f("ck_sources_ready_has_text"),
        ),
        sa.CheckConstraint(
            "extraction_state IN ('pending', 'ready', 'failed')",
            name=op.f("ck_sources_valid_extraction_state"),
        ),
        sa.CheckConstraint(
            "kind IN ('file', 'url', 'text')", name=op.f("ck_sources_valid_kind")
        ),
        sa.CheckConstraint(
            "reviewed_at IS NULL OR extraction_state = 'ready'",
            name=op.f("ck_sources_review_requires_text"),
        ),
        sa.CheckConstraint(
            "length(btrim(display_name)) > 0", name=op.f("ck_sources_name_not_blank")
        ),
        sa.ForeignKeyConstraint(
            ["definition_id"],
            ["job_definitions.id"],
            name=op.f("fk_sources_definition_id_job_definitions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sources")),
        sa.UniqueConstraint(
            "definition_id", "file_slot", name=op.f("uq_sources_definition_id")
        ),
        sa.UniqueConstraint("object_key", name=op.f("uq_sources_object_key")),
    )
    op.create_index(
        op.f("ix_sources_definition_id"), "sources", ["definition_id"], unique=False
    )
    op.create_table(
        "background_facts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(btrim(content)) > 0",
            name=op.f("ck_background_facts_content_not_blank"),
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["sources.id"],
            name=op.f("fk_background_facts_source_id_sources"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_background_facts")),
    )
    op.create_index(
        op.f("ix_background_facts_source_id"),
        "background_facts",
        ["source_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_background_facts_source_id"), table_name="background_facts")
    op.drop_table("background_facts")
    op.drop_index(op.f("ix_sources_definition_id"), table_name="sources")
    op.drop_table("sources")
    op.drop_index(op.f("ix_preferences_definition_id"), table_name="preferences")
    op.drop_table("preferences")
    op.drop_index(op.f("ix_clarifications_definition_id"), table_name="clarifications")
    op.drop_table("clarifications")
    op.drop_table("job_definitions")
    op.drop_table("owners")
