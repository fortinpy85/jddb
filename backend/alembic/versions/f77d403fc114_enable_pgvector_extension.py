"""enable_pgvector_extension

Enable the pgvector extension for PostgreSQL.
This must run before the first migration that creates tables with VECTOR columns.

Revision ID: f77d403fc114
Revises: None (this should be the FIRST migration)
Create Date: 2025-10-20 16:37:45.855708

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f77d403fc114'
down_revision = None  # This is now the first migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension for PostgreSQL
    # Use IF NOT EXISTS to avoid errors if already enabled
    op.execute(sa.text('CREATE EXTENSION IF NOT EXISTS vector'))


def downgrade() -> None:
    # Disable pgvector extension
    # CASCADE will drop all dependent objects (VECTOR columns)
    op.execute(sa.text('DROP EXTENSION IF EXISTS vector CASCADE'))
