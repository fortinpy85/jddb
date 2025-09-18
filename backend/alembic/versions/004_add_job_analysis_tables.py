"""Add job analysis tables for comparison and skill analysis

Revision ID: 004
Revises: 003
Create Date: 2025-09-12 16:20:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "004"
down_revision = "fba902742fb7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Job comparison results cache
    op.create_table(
        "job_comparisons",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_a_id", sa.Integer(), nullable=False),
        sa.Column("job_b_id", sa.Integer(), nullable=False),
        sa.Column("comparison_type", sa.String(50), nullable=False),
        sa.Column("overall_score", sa.Numeric(4, 3), nullable=True),
        sa.Column(
            "section_scores", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "metadata_comparison",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "skills_analysis", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["job_a_id"],
            ["job_descriptions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["job_b_id"],
            ["job_descriptions.id"],
        ),
        sa.UniqueConstraint(
            "job_a_id", "job_b_id", "comparison_type", name="uq_job_comparison"
        ),
    )

    # Create indexes for job comparisons
    op.create_index("idx_job_comparisons_job_a", "job_comparisons", ["job_a_id"])
    op.create_index("idx_job_comparisons_job_b", "job_comparisons", ["job_b_id"])
    op.create_index("idx_job_comparisons_type", "job_comparisons", ["comparison_type"])

    # Extracted skills from job descriptions
    op.create_table(
        "job_skills",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("skill_category", sa.String(100), nullable=False),
        sa.Column("skill_name", sa.String(200), nullable=False),
        sa.Column("skill_level", sa.String(50), nullable=False),
        sa.Column("confidence_score", sa.Numeric(4, 3), nullable=True),
        sa.Column("extracted_from_section", sa.String(50), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["job_descriptions.id"],
        ),
    )

    # Create indexes for job skills
    op.create_index("idx_job_skills_job_id", "job_skills", ["job_id"])
    op.create_index("idx_job_skills_category", "job_skills", ["skill_category"])
    op.create_index("idx_job_skills_name", "job_skills", ["skill_name"])

    # Career path analysis cache
    op.create_table(
        "career_paths",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("from_job_id", sa.Integer(), nullable=False),
        sa.Column("to_job_id", sa.Integer(), nullable=False),
        sa.Column("progression_type", sa.String(50), nullable=False),
        sa.Column("feasibility_score", sa.Numeric(4, 3), nullable=True),
        sa.Column(
            "skill_gap_analysis", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("required_experience_years", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["from_job_id"],
            ["job_descriptions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["to_job_id"],
            ["job_descriptions.id"],
        ),
        sa.UniqueConstraint("from_job_id", "to_job_id", name="uq_career_path"),
    )

    # Create indexes for career paths
    op.create_index("idx_career_paths_from", "career_paths", ["from_job_id"])
    op.create_index("idx_career_paths_to", "career_paths", ["to_job_id"])
    op.create_index("idx_career_paths_type", "career_paths", ["progression_type"])

    # Classification benchmark data
    op.create_table(
        "classification_benchmarks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("classification", sa.String(10), nullable=False),
        sa.Column("department", sa.String(200), nullable=True),
        sa.Column("avg_salary", sa.Numeric(), nullable=True),
        sa.Column("median_salary", sa.Numeric(), nullable=True),
        sa.Column("avg_fte_supervised", sa.Integer(), nullable=True),
        sa.Column(
            "common_skills", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("typical_reports_to", sa.String(500), nullable=True),
        sa.Column("job_count", sa.Integer(), nullable=True),
        sa.Column(
            "last_updated",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "classification", "department", name="uq_classification_benchmark"
        ),
    )

    # Create indexes for classification benchmarks
    op.create_index(
        "idx_classification_benchmarks_class",
        "classification_benchmarks",
        ["classification"],
    )
    op.create_index(
        "idx_classification_benchmarks_dept",
        "classification_benchmarks",
        ["department"],
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table("classification_benchmarks")
    op.drop_table("career_paths")
    op.drop_table("job_skills")
    op.drop_table("job_comparisons")
