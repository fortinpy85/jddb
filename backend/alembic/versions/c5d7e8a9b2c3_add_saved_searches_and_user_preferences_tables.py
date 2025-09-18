"""Add saved searches and user preferences tables

Revision ID: c5d7e8a9b2c3
Revises: 70359207d894
Create Date: 2025-09-13 15:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "c5d7e8a9b2c3"
down_revision = "70359207d894"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create saved_searches table
    op.create_table(
        "saved_searches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("user_id", sa.String(length=100), nullable=True),
        sa.Column("session_id", sa.String(length=100), nullable=True),
        sa.Column("search_query", sa.Text(), nullable=True),
        sa.Column("search_type", sa.String(length=50), nullable=True, default="text"),
        sa.Column(
            "search_filters", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("is_public", sa.String(length=10), nullable=True, default="private"),
        sa.Column("is_favorite", sa.String(length=10), nullable=True, default="false"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=True, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=True, server_default=sa.func.now()
        ),
        sa.Column(
            "last_used", sa.DateTime(), nullable=True, server_default=sa.func.now()
        ),
        sa.Column("use_count", sa.Integer(), nullable=True, default=0),
        sa.Column("last_result_count", sa.Integer(), nullable=True),
        sa.Column("last_execution_time_ms", sa.Integer(), nullable=True),
        sa.Column(
            "search_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for saved_searches
    op.create_index("ix_saved_searches_user_id", "saved_searches", ["user_id"])
    op.create_index("ix_saved_searches_session_id", "saved_searches", ["session_id"])
    op.create_index("ix_saved_searches_is_public", "saved_searches", ["is_public"])
    op.create_index("ix_saved_searches_is_favorite", "saved_searches", ["is_favorite"])
    op.create_index("ix_saved_searches_last_used", "saved_searches", ["last_used"])
    op.create_index("ix_saved_searches_use_count", "saved_searches", ["use_count"])

    # Create user_preferences table
    op.create_table(
        "user_preferences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(length=100), nullable=True),
        sa.Column("session_id", sa.String(length=100), nullable=True),
        sa.Column("preference_type", sa.String(length=50), nullable=True),
        sa.Column("preference_key", sa.String(length=100), nullable=True),
        sa.Column(
            "preference_value", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "created_at", sa.DateTime(), nullable=True, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=True, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "session_id",
            "preference_type",
            "preference_key",
            name="uq_user_preference",
        ),
    )

    # Create indexes for user_preferences
    op.create_index("ix_user_preferences_user_id", "user_preferences", ["user_id"])
    op.create_index(
        "ix_user_preferences_session_id", "user_preferences", ["session_id"]
    )
    op.create_index("ix_user_preferences_type", "user_preferences", ["preference_type"])


def downgrade() -> None:
    # Drop indexes first
    op.drop_index("ix_user_preferences_type", table_name="user_preferences")
    op.drop_index("ix_user_preferences_session_id", table_name="user_preferences")
    op.drop_index("ix_user_preferences_user_id", table_name="user_preferences")

    op.drop_index("ix_saved_searches_use_count", table_name="saved_searches")
    op.drop_index("ix_saved_searches_last_used", table_name="saved_searches")
    op.drop_index("ix_saved_searches_is_favorite", table_name="saved_searches")
    op.drop_index("ix_saved_searches_is_public", table_name="saved_searches")
    op.drop_index("ix_saved_searches_session_id", table_name="saved_searches")
    op.drop_index("ix_saved_searches_user_id", table_name="saved_searches")

    # Drop tables
    op.drop_table("user_preferences")
    op.drop_table("saved_searches")
