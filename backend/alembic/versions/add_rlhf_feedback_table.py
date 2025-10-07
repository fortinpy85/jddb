"""Add RLHF feedback table

Revision ID: add_rlhf_feedback
Revises:
Create Date: 2025-10-03

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "add_rlhf_feedback"
down_revision = "9063ab14ed70"  # Current head revision
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create RLHF feedback table"""
    op.create_table(
        "rlhf_feedback",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("job_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("original_text", sa.Text(), nullable=False),
        sa.Column("suggested_text", sa.Text(), nullable=True),
        sa.Column("final_text", sa.Text(), nullable=True),
        sa.Column("suggestion_type", sa.String(length=50), nullable=True),
        sa.Column("user_action", sa.String(length=50), nullable=False),
        sa.Column("confidence", sa.DECIMAL(precision=4, scale=3), nullable=True),
        sa.Column(
            "feedback_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.ForeignKeyConstraint(
            ["job_id"], ["job_descriptions.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for better query performance
    op.create_index("ix_rlhf_feedback_event_type", "rlhf_feedback", ["event_type"])
    op.create_index(
        "ix_rlhf_feedback_suggestion_type", "rlhf_feedback", ["suggestion_type"]
    )
    op.create_index("ix_rlhf_feedback_user_action", "rlhf_feedback", ["user_action"])
    op.create_index("ix_rlhf_feedback_created_at", "rlhf_feedback", ["created_at"])
    op.create_index("ix_rlhf_feedback_user_id", "rlhf_feedback", ["user_id"])
    op.create_index("ix_rlhf_feedback_job_id", "rlhf_feedback", ["job_id"])


def downgrade() -> None:
    """Drop RLHF feedback table"""
    op.drop_index("ix_rlhf_feedback_job_id", table_name="rlhf_feedback")
    op.drop_index("ix_rlhf_feedback_user_id", table_name="rlhf_feedback")
    op.drop_index("ix_rlhf_feedback_created_at", table_name="rlhf_feedback")
    op.drop_index("ix_rlhf_feedback_user_action", table_name="rlhf_feedback")
    op.drop_index("ix_rlhf_feedback_suggestion_type", table_name="rlhf_feedback")
    op.drop_index("ix_rlhf_feedback_event_type", table_name="rlhf_feedback")
    op.drop_table("rlhf_feedback")
