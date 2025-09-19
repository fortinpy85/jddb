"""Optimize vector indexes for performance

Revision ID: 014_optimize_vector_indexes
Revises: 013_add_search_analytics
Create Date: 2024-09-13 10:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "014_optimize_vector_indexes"
down_revision = "400307a1032c"
branch_labels = None
depends_on = None


def upgrade():
    """Add optimized indexes for vector search performance."""

    # Create HNSW index for content_chunks embeddings (optimized for similarity search)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_content_chunks_embedding_hnsw
        ON content_chunks
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    """
    )

    # Create IVFFlat index as fallback (better for smaller datasets)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_content_chunks_embedding_ivfflat
        ON content_chunks
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
    """
    )

    # Composite index for filtered searches (optimized without embedding column)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_chunks_job_id_with_embedding
        ON content_chunks (job_id)
        WHERE embedding IS NOT NULL;
    """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_jobs_classification_language
        ON job_descriptions (classification, language);
    """
    )

    # Optimize job_descriptions indexes for joins (simplified without INCLUDE)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_jobs_id_title_classification
        ON job_descriptions (id, title, classification, language, job_number);
    """
    )

    # Index for efficient chunk counting
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_chunks_job_id_has_embedding
        ON content_chunks (job_id, (embedding IS NOT NULL));
    """
    )

    # Partial index for non-null embeddings only
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_chunks_has_embedding
        ON content_chunks (id)
        WHERE embedding IS NOT NULL;
    """
    )

    # Set statistics target for better query planning
    op.execute(
        """
        ALTER TABLE content_chunks ALTER COLUMN embedding SET STATISTICS 1000;
    """
    )

    # Create statistics for multi-column queries
    op.execute(
        """
        CREATE STATISTICS IF NOT EXISTS stats_chunks_job_embedding
        (dependencies) ON job_id, embedding FROM content_chunks;
    """
    )


def downgrade():
    """Remove optimized vector indexes."""

    # Drop statistics
    op.execute("DROP STATISTICS IF EXISTS stats_chunks_job_embedding;")

    # Reset statistics target
    op.execute("ALTER TABLE content_chunks ALTER COLUMN embedding SET STATISTICS -1;")

    # Drop indexes (in reverse order)
    op.execute("DROP INDEX IF EXISTS idx_chunks_has_embedding;")
    op.execute("DROP INDEX IF EXISTS idx_chunks_job_id_has_embedding;")
    op.execute("DROP INDEX IF EXISTS idx_jobs_id_title_classification;")
    op.execute("DROP INDEX IF EXISTS idx_jobs_classification_language;")
    op.execute("DROP INDEX IF EXISTS idx_chunks_job_id_embedding;")
    op.execute(
        "DROP INDEX IF EXISTS idx_content_chunks_embedding_ivfflat;"
    )
    op.execute("DROP INDEX IF EXISTS idx_content_chunks_embedding_hnsw;")
