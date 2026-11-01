"""Private sessions and durable source processing status.

Revision ID: 0003
Revises: 0002
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "owners",
        sa.Column("failed_logins", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("owners", sa.Column("locked_until", sa.DateTime(timezone=True)))
    op.create_table(
        "owner_sessions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "owner_id",
            sa.SmallInteger(),
            sa.ForeignKey("owners.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_owner_sessions_expires_at", "owner_sessions", ["expires_at"])
    op.add_column(
        "sources",
        sa.Column(
            "original_stored", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    # Originals from Part 5 were durable before their extraction became ready.
    op.execute(
        "UPDATE sources SET original_stored = true "
        "WHERE kind = 'file' AND extraction_state = 'ready'"
    )
    op.add_column(
        "sources", sa.Column("extraction_error", postgresql.JSONB(none_as_null=True))
    )


def downgrade() -> None:
    op.drop_column("sources", "extraction_error")
    op.drop_column("sources", "original_stored")
    op.drop_table("owner_sessions")
    op.drop_column("owners", "locked_until")
    op.drop_column("owners", "failed_logins")
