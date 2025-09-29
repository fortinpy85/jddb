"""add_pgvector_indexes_for_performance

Revision ID: 70359207d894
Revises: b6ccdf00a4c0
Create Date: 2025-09-13 12:32:01.509394

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "70359207d894"
down_revision = "b6ccdf00a4c0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create HNSW index for vector similarity searches (fastest for large datasets)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_content_chunks_embedding_hnsw
        ON content_chunks USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    """
    )

    # Create IVFFlat index as alternative (better for smaller datasets)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_content_chunks_embedding_ivfflat
        ON content_chunks USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
    """
    )

    # Add regular database indexes for commonly filtered columns
    op.create_index("idx_content_chunks_job_id", "content_chunks", ["job_id"])
    op.create_index(
        "idx_job_descriptions_classification", "job_descriptions", ["classification"]
    )
    op.create_index("idx_job_descriptions_language", "job_descriptions", ["language"])
    op.create_index("idx_job_descriptions_title", "job_descriptions", ["title"])

    # Composite index for common search patterns
    op.create_index(
        "idx_job_desc_class_lang", "job_descriptions", ["classification", "language"]
    )

    # Analytics table indexes for performance
    op.create_index("idx_usage_analytics_timestamp", "usage_analytics", ["timestamp"])
    op.create_index(
        "idx_usage_analytics_action_type", "usage_analytics", ["action_type"]
    )
    op.create_index("idx_usage_analytics_session_id", "usage_analytics", ["session_id"])

    op.create_index(
        "idx_ai_usage_tracking_timestamp", "ai_usage_tracking", ["request_timestamp"]
    )
    op.create_index(
        "idx_ai_usage_tracking_service_type", "ai_usage_tracking", ["service_type"]
    )

    op.create_index("idx_system_metrics_timestamp", "system_metrics", ["timestamp"])
    op.create_index("idx_system_metrics_metric_type", "system_metrics", ["metric_type"])


def downgrade() -> None:
    # Drop regular indexes
    op.drop_index("idx_system_metrics_metric_type")
    op.drop_index("idx_system_metrics_timestamp")
    op.drop_index("idx_ai_usage_tracking_service_type")
    op.drop_index("idx_ai_usage_tracking_timestamp")
    op.drop_index("idx_usage_analytics_session_id")
    op.drop_index("idx_usage_analytics_action_type")
    op.drop_index("idx_usage_analytics_timestamp")
    op.drop_index("idx_job_desc_class_lang")
    op.drop_index("idx_job_descriptions_title")
    op.drop_index("idx_job_descriptions_language")
    op.drop_index("idx_job_descriptions_classification")
    op.drop_index("idx_content_chunks_job_id")

    # Drop vector indexes
    op.execute("DROP INDEX IF EXISTS idx_content_chunks_embedding_ivfflat;")
    op.execute("DROP INDEX IF EXISTS idx_content_chunks_embedding_hnsw;")
