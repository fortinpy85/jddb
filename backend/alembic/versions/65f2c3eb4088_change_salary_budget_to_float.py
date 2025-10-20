"""change_salary_budget_to_float

Change job_metadata.salary_budget from NUMERIC to Float type for better
compatibility with SQLAlchemy's Float type mapping.

Revision ID: 65f2c3eb4088
Revises: 0e13c9b0cf72
Create Date: 2025-10-20 16:40:42.259411

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "65f2c3eb4088"
down_revision = "0e13c9b0cf72"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Change salary_budget column type from NUMERIC to Float
    # This aligns the database schema with the SQLAlchemy model definition
    op.alter_column(
        "job_metadata",
        "salary_budget",
        existing_type=sa.NUMERIC(),
        type_=sa.Float(),
        existing_nullable=True,
    )


def downgrade() -> None:
    # Revert salary_budget column type back to NUMERIC
    op.alter_column(
        "job_metadata",
        "salary_budget",
        existing_type=sa.Float(),
        type_=sa.NUMERIC(),
        existing_nullable=True,
    )
