"""Add user authentication tables

Revision ID: 9063ab14ed70
Revises: 6375fbf9a927
Create Date: 2025-09-28 22:43:56.499250

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9063ab14ed70"
down_revision = "6375fbf9a927"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table if it doesn't exist (handles fresh CI/CD databases)
    from sqlalchemy import inspect

    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()

    if "users" not in existing_tables:
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("username", sa.String(), nullable=False),
            sa.Column("email", sa.String(), nullable=False),
            sa.Column("password_hash", sa.String(), nullable=False),
            sa.Column("first_name", sa.String(), nullable=True),
            sa.Column("last_name", sa.String(), nullable=True),
            sa.Column("role", sa.String(), nullable=False),
            sa.Column("department", sa.String(), nullable=True),
            sa.Column("security_clearance", sa.String(), nullable=True),
            sa.Column("preferred_language", sa.String(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("last_login", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
        op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
        op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    if "user_sessions" not in existing_tables:
        op.create_table(
            "user_sessions",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("session_token", sa.String(), nullable=False),
            sa.Column("ip_address", sa.String(), nullable=True),
            sa.Column("user_agent", sa.String(), nullable=True),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("last_activity", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(
                ["user_id"],
                ["users.id"],
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_user_sessions_id"), "user_sessions", ["id"], unique=False
        )
        op.create_index(
            op.f("ix_user_sessions_session_token"),
            "user_sessions",
            ["session_token"],
            unique=True,
        )

    if "user_permissions" not in existing_tables:
        op.create_table(
            "user_permissions",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("resource_type", sa.String(), nullable=False),
            sa.Column("resource_id", sa.Integer(), nullable=True),
            sa.Column("permission_type", sa.String(), nullable=False),
            sa.Column("granted_by", sa.Integer(), nullable=True),
            sa.Column("granted_at", sa.DateTime(), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(
                ["user_id"],
                ["users.id"],
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_user_permissions_id"), "user_permissions", ["id"], unique=False
        )

    if "user_preferences" not in existing_tables:
        op.create_table(
            "user_preferences",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("preference_key", sa.String(), nullable=False),
            sa.Column("preference_value", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(
                ["user_id"],
                ["users.id"],
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_user_preferences_id"), "user_preferences", ["id"], unique=False
        )


def downgrade() -> None:
    op.drop_index(op.f("ix_user_preferences_id"), table_name="user_preferences")
    op.drop_table("user_preferences")
    op.drop_index(op.f("ix_user_permissions_id"), table_name="user_permissions")
    op.drop_table("user_permissions")
    op.drop_index(op.f("ix_user_sessions_session_token"), table_name="user_sessions")
    op.drop_index(op.f("ix_user_sessions_id"), table_name="user_sessions")
    op.drop_table("user_sessions")
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
