"""Add retryable deletion of original documents.

Revision ID: 0002
Revises: 0001
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "document_deletions",
        sa.Column("object_key", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("object_key", name=op.f("pk_document_deletions")),
    )


def downgrade() -> None:
    op.drop_table("document_deletions")
