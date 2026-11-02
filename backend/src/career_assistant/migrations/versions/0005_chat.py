"""Persistent chat turns attached to the current definition.

Revision ID: 0005
Revises: 0004
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chat_turns",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "definition_id",
            sa.Uuid(),
            sa.ForeignKey("job_definitions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("language", sa.Text(), nullable=False),
        sa.Column("response", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "length(btrim(message)) BETWEEN 1 AND 4000",
            name=op.f("ck_chat_turns_message_length"),
        ),
    )
    op.create_index("ix_chat_turns_definition_id", "chat_turns", ["definition_id"])


def downgrade() -> None:
    op.drop_table("chat_turns")
