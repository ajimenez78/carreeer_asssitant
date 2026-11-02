"""Saved clarity assessments and user-controlled clarification pauses.

Revision ID: 0004
Revises: 0003
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "job_definitions",
        sa.Column("assessment", postgresql.JSONB(none_as_null=True)),
    )
    op.add_column(
        "job_definitions",
        sa.Column(
            "clarification_paused",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "job_definitions",
        sa.Column("control_version", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_check_constraint(
        op.f("ck_job_definitions_valid_control_version"),
        "job_definitions",
        "control_version >= 0",
    )
    # Existing user-selected readiness is not a system assessment.
    op.execute("UPDATE job_definitions SET state = 'draft'")


def downgrade() -> None:
    op.drop_constraint(
        op.f("ck_job_definitions_valid_control_version"),
        "job_definitions",
        type_="check",
    )
    op.drop_column("job_definitions", "control_version")
    op.drop_column("job_definitions", "clarification_paused")
    op.drop_column("job_definitions", "assessment")
