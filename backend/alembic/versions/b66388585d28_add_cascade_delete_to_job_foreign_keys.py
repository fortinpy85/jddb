"""add_cascade_delete_to_job_foreign_keys

Revision ID: b66388585d28
Revises: 465a48a9e37f
Create Date: 2025-10-10 21:39:29.618999

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "b66388585d28"  # pragma: allowlist secret
down_revision = "465a48a9e37f"  # pragma: allowlist secret
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add CASCADE delete to all foreign keys referencing job_descriptions."""

    # job_sections.job_id
    op.drop_constraint("job_sections_job_id_fkey", "job_sections", type_="foreignkey")
    op.create_foreign_key(
        "job_sections_job_id_fkey",
        "job_sections",
        "job_descriptions",
        ["job_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # job_metadata.job_id
    op.drop_constraint("job_metadata_job_id_fkey", "job_metadata", type_="foreignkey")
    op.create_foreign_key(
        "job_metadata_job_id_fkey",
        "job_metadata",
        "job_descriptions",
        ["job_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # content_chunks.job_id
    op.drop_constraint(
        "content_chunks_job_id_fkey", "content_chunks", type_="foreignkey"
    )
    op.create_foreign_key(
        "content_chunks_job_id_fkey",
        "content_chunks",
        "job_descriptions",
        ["job_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # data_quality_metrics.job_id
    op.drop_constraint(
        "data_quality_metrics_job_id_fkey", "data_quality_metrics", type_="foreignkey"
    )
    op.create_foreign_key(
        "data_quality_metrics_job_id_fkey",
        "data_quality_metrics",
        "job_descriptions",
        ["job_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # job_comparisons.job1_id
    op.drop_constraint(
        "job_comparisons_job1_id_fkey", "job_comparisons", type_="foreignkey"
    )
    op.create_foreign_key(
        "job_comparisons_job1_id_fkey",
        "job_comparisons",
        "job_descriptions",
        ["job1_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # job_comparisons.job2_id
    op.drop_constraint(
        "job_comparisons_job2_id_fkey", "job_comparisons", type_="foreignkey"
    )
    op.create_foreign_key(
        "job_comparisons_job2_id_fkey",
        "job_comparisons",
        "job_descriptions",
        ["job2_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # job_skills.job_id (deprecated table but still present)
    op.drop_constraint("job_skills_job_id_fkey", "job_skills", type_="foreignkey")
    op.create_foreign_key(
        "job_skills_job_id_fkey",
        "job_skills",
        "job_descriptions",
        ["job_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # rlhf_feedback.job_id - currently SET NULL, change to CASCADE
    op.drop_constraint("rlhf_feedback_job_id_fkey", "rlhf_feedback", type_="foreignkey")
    op.create_foreign_key(
        "rlhf_feedback_job_id_fkey",
        "rlhf_feedback",
        "job_descriptions",
        ["job_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """Revert CASCADE delete changes."""

    # Revert job_sections.job_id
    op.drop_constraint("job_sections_job_id_fkey", "job_sections", type_="foreignkey")
    op.create_foreign_key(
        "job_sections_job_id_fkey",
        "job_sections",
        "job_descriptions",
        ["job_id"],
        ["id"],
    )

    # Revert job_metadata.job_id
    op.drop_constraint("job_metadata_job_id_fkey", "job_metadata", type_="foreignkey")
    op.create_foreign_key(
        "job_metadata_job_id_fkey",
        "job_metadata",
        "job_descriptions",
        ["job_id"],
        ["id"],
    )

    # Revert content_chunks.job_id
    op.drop_constraint(
        "content_chunks_job_id_fkey", "content_chunks", type_="foreignkey"
    )
    op.create_foreign_key(
        "content_chunks_job_id_fkey",
        "content_chunks",
        "job_descriptions",
        ["job_id"],
        ["id"],
    )

    # Revert data_quality_metrics.job_id
    op.drop_constraint(
        "data_quality_metrics_job_id_fkey", "data_quality_metrics", type_="foreignkey"
    )
    op.create_foreign_key(
        "data_quality_metrics_job_id_fkey",
        "data_quality_metrics",
        "job_descriptions",
        ["job_id"],
        ["id"],
    )

    # Revert job_comparisons.job1_id
    op.drop_constraint(
        "job_comparisons_job1_id_fkey", "job_comparisons", type_="foreignkey"
    )
    op.create_foreign_key(
        "job_comparisons_job1_id_fkey",
        "job_comparisons",
        "job_descriptions",
        ["job1_id"],
        ["id"],
    )

    # Revert job_comparisons.job2_id
    op.drop_constraint(
        "job_comparisons_job2_id_fkey", "job_comparisons", type_="foreignkey"
    )
    op.create_foreign_key(
        "job_comparisons_job2_id_fkey",
        "job_comparisons",
        "job_descriptions",
        ["job2_id"],
        ["id"],
    )

    # Revert job_skills.job_id
    op.drop_constraint("job_skills_job_id_fkey", "job_skills", type_="foreignkey")
    op.create_foreign_key(
        "job_skills_job_id_fkey", "job_skills", "job_descriptions", ["job_id"], ["id"]
    )

    # Revert rlhf_feedback.job_id back to SET NULL
    op.drop_constraint("rlhf_feedback_job_id_fkey", "rlhf_feedback", type_="foreignkey")
    op.create_foreign_key(
        "rlhf_feedback_job_id_fkey",
        "rlhf_feedback",
        "job_descriptions",
        ["job_id"],
        ["id"],
        ondelete="SET NULL",
    )
