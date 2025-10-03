"""
Tests for database models.
"""

from jd_ingestion.database.models import (
    Base,
    JobDescription,
    JobSection,
    ContentChunk,
    JobMetadata,
    JobComparison,
    JobSkill,
    # CareerPath,  # Removed
    # ClassificationBenchmark,  # Removed
    DataQualityMetrics,
    AIUsageTracking,
    UsageAnalytics,
    SystemMetrics,
    SavedSearch,
    UserPreference,
    SearchAnalytics,
    # TranslationProject,  # Removed
    # TranslationMemory,  # Removed
    # TranslationEmbedding,  # Removed
)


class TestBaseModel:
    """Test base model functionality."""

    def test_base_inheritance(self):
        """Test that all models inherit from Base."""
        models = [
            JobDescription,
            JobSection,
            ContentChunk,
            JobMetadata,
            JobComparison,
            JobSkill,
            # CareerPath,  # Removed
            # ClassificationBenchmark,  # Removed
            DataQualityMetrics,
            AIUsageTracking,
            UsageAnalytics,
            SystemMetrics,
            SavedSearch,
            UserPreference,
            SearchAnalytics,
            # TranslationProject,  # Removed
            # TranslationMemory,  # Removed
            # TranslationEmbedding,  # Removed
        ]

        for model in models:
            assert issubclass(model, Base)
            assert hasattr(model, "__tablename__")


class TestJobDescription:
    """Test JobDescription model."""

    def test_table_name(self):
        """Test table name is correct."""
        assert JobDescription.__tablename__ == "job_descriptions"

    def test_columns(self):
        """Test that required columns exist."""
        model = JobDescription
        assert hasattr(model, "id")
        assert hasattr(model, "job_number")
        assert hasattr(model, "title")
        assert hasattr(model, "classification")
        assert hasattr(model, "language")
        assert hasattr(model, "file_path")
        assert hasattr(model, "raw_content")
        assert hasattr(model, "processed_date")
        assert hasattr(model, "file_hash")
        assert hasattr(model, "created_at")
        assert hasattr(model, "updated_at")

    def test_relationships(self):
        """Test that relationships are defined."""
        model = JobDescription
        assert hasattr(model, "sections")
        assert hasattr(model, "metadata_entry")
        assert hasattr(model, "chunks")

    def test_indexes(self):
        """Test that indexes are properly defined."""
        indexes = JobDescription.__table_args__
        assert len(indexes) == 5  # 5 indexes defined

    def test_unique_constraint(self):
        """Test job_number unique constraint."""
        job_number_column = None
        for column in JobDescription.__table__.columns:
            if column.name == "job_number":
                job_number_column = column
                break

        assert job_number_column is not None
        assert job_number_column.unique is True


class TestJobSection:
    """Test JobSection model."""

    def test_table_name(self):
        """Test table name is correct."""
        assert JobSection.__tablename__ == "job_sections"

    def test_columns(self):
        """Test that required columns exist."""
        model = JobSection
        assert hasattr(model, "id")
        assert hasattr(model, "job_id")
        assert hasattr(model, "section_type")
        assert hasattr(model, "section_content")
        assert hasattr(model, "section_order")

    def test_relationships(self):
        """Test that relationships are defined."""
        model = JobSection
        assert hasattr(model, "job")
        assert hasattr(model, "chunks")

    def test_foreign_key(self):
        """Test foreign key relationship to job_descriptions."""
        job_id_column = None
        for column in JobSection.__table__.columns:
            if column.name == "job_id":
                job_id_column = column
                break

        assert job_id_column is not None
        assert len(job_id_column.foreign_keys) == 1


class TestContentChunk:
    """Test ContentChunk model."""

    def test_table_name(self):
        """Test table name is correct."""
        assert ContentChunk.__tablename__ == "content_chunks"

    def test_columns(self):
        """Test that required columns exist."""
        model = ContentChunk
        assert hasattr(model, "id")
        assert hasattr(model, "job_id")
        assert hasattr(model, "section_id")
        assert hasattr(model, "chunk_text")
        assert hasattr(model, "chunk_index")
        assert hasattr(model, "embedding")

    def test_relationships(self):
        """Test that relationships are defined."""
        model = ContentChunk
        assert hasattr(model, "job")
        assert hasattr(model, "section")

    def test_foreign_keys(self):
        """Test foreign key relationships."""
        job_id_column = None
        section_id_column = None

        for column in ContentChunk.__table__.columns:
            if column.name == "job_id":
                job_id_column = column
            elif column.name == "section_id":
                section_id_column = column

        assert job_id_column is not None
        assert section_id_column is not None
        assert len(job_id_column.foreign_keys) == 1
        assert len(section_id_column.foreign_keys) == 1


class TestJobMetadata:
    """Test JobMetadata model."""

    def test_table_name(self):
        """Test table name is correct."""
        assert JobMetadata.__tablename__ == "job_metadata"

    def test_columns(self):
        """Test that required columns exist."""
        model = JobMetadata
        assert hasattr(model, "id")
        assert hasattr(model, "job_id")
        assert hasattr(model, "reports_to")
        assert hasattr(model, "department")
        assert hasattr(model, "location")
        assert hasattr(model, "fte_count")
        assert hasattr(model, "salary_budget")
        assert hasattr(model, "effective_date")

    def test_relationships(self):
        """Test that relationships are defined."""
        model = JobMetadata
        assert hasattr(model, "job")

    def test_indexes(self):
        """Test that indexes are properly defined."""
        indexes = JobMetadata.__table_args__
        assert len(indexes) == 2  # 2 indexes defined


class TestJobComparison:
    """Test JobComparison model."""

    def test_table_name(self):
        """Test table name is correct."""
        assert JobComparison.__tablename__ == "job_comparisons"

    def test_columns(self):
        """Test that required columns exist."""
        model = JobComparison
        assert hasattr(model, "id")
        assert hasattr(model, "job_a_id")
        assert hasattr(model, "job_b_id")
        assert hasattr(model, "comparison_type")
        assert hasattr(model, "overall_score")
        assert hasattr(model, "section_scores")
        assert hasattr(model, "metadata_comparison")
        assert hasattr(model, "skills_analysis")
        assert hasattr(model, "created_at")
        assert hasattr(model, "updated_at")

    def test_relationships(self):
        """Test that relationships are defined."""
        model = JobComparison
        assert hasattr(model, "job_a")
        assert hasattr(model, "job_b")

    def test_unique_constraint(self):
        """Test unique constraint on job comparison."""
        constraints = JobComparison.__table_args__
        assert len(constraints) == 1
        constraint = constraints[0]
        assert constraint.name == "uq_job_comparison"


class TestDataQualityMetrics:
    """Test DataQualityMetrics model."""

    def test_table_name(self):
        """Test table name is correct."""
        assert DataQualityMetrics.__tablename__ == "data_quality_metrics"

    def test_columns(self):
        """Test that required columns exist."""
        model = DataQualityMetrics
        assert hasattr(model, "id")
        assert hasattr(model, "job_id")
        assert hasattr(model, "content_completeness_score")
        assert hasattr(model, "sections_completeness_score")
        assert hasattr(model, "metadata_completeness_score")
        assert hasattr(model, "has_structured_fields")
        assert hasattr(model, "has_all_sections")
        assert hasattr(model, "has_embeddings")
        assert hasattr(model, "processing_errors_count")
        assert hasattr(model, "validation_errors_count")
        assert hasattr(model, "validation_results")
        assert hasattr(model, "quality_flags")

    def test_relationships(self):
        """Test that relationships are defined."""
        model = DataQualityMetrics
        assert hasattr(model, "job")

    def test_unique_job_id(self):
        """Test that job_id is unique."""
        job_id_column = None
        for column in DataQualityMetrics.__table__.columns:
            if column.name == "job_id":
                job_id_column = column
                break

        assert job_id_column is not None
        assert job_id_column.unique is True


class TestAIUsageTracking:
    """Test AIUsageTracking model."""

    def test_table_name(self):
        """Test table name is correct."""
        assert AIUsageTracking.__tablename__ == "ai_usage_tracking"

    def test_columns(self):
        """Test that required columns exist."""
        model = AIUsageTracking
        assert hasattr(model, "id")
        assert hasattr(model, "request_timestamp")
        assert hasattr(model, "service_type")
        assert hasattr(model, "operation_type")
        assert hasattr(model, "input_tokens")
        assert hasattr(model, "output_tokens")
        assert hasattr(model, "total_tokens")
        assert hasattr(model, "cost_usd")
        assert hasattr(model, "request_id")
        assert hasattr(model, "model_name")
        assert hasattr(model, "success")
        assert hasattr(model, "error_message")
        assert hasattr(model, "request_metadata")


class TestUsageAnalytics:
    """Test UsageAnalytics model."""

    def test_table_name(self):
        """Test table name is correct."""
        assert UsageAnalytics.__tablename__ == "usage_analytics"

    def test_columns(self):
        """Test that required columns exist."""
        model = UsageAnalytics
        assert hasattr(model, "id")
        assert hasattr(model, "timestamp")
        assert hasattr(model, "session_id")
        assert hasattr(model, "user_id")
        assert hasattr(model, "ip_address")
        assert hasattr(model, "user_agent")
        assert hasattr(model, "action_type")
        assert hasattr(model, "endpoint")
        assert hasattr(model, "http_method")
        assert hasattr(model, "resource_id")
        assert hasattr(model, "response_time_ms")
        assert hasattr(model, "status_code")


class TestSystemMetrics:
    """Test SystemMetrics model."""

    def test_table_name(self):
        """Test table name is correct."""
        assert SystemMetrics.__tablename__ == "system_metrics"

    def test_columns(self):
        """Test that required columns exist."""
        model = SystemMetrics
        assert hasattr(model, "id")
        assert hasattr(model, "timestamp")
        assert hasattr(model, "metric_type")
        assert hasattr(model, "total_requests")
        assert hasattr(model, "unique_sessions")
        assert hasattr(model, "avg_response_time_ms")
        assert hasattr(model, "error_rate")
        assert hasattr(model, "total_ai_requests")
        assert hasattr(model, "total_tokens_used")
        assert hasattr(model, "total_ai_cost_usd")
        assert hasattr(model, "detailed_metrics")


class TestSavedSearch:
    """Test SavedSearch model."""

    def test_table_name(self):
        """Test table name is correct."""
        assert SavedSearch.__tablename__ == "saved_searches"

    def test_columns(self):
        """Test that required columns exist."""
        model = SavedSearch
        assert hasattr(model, "id")
        assert hasattr(model, "name")
        assert hasattr(model, "description")
        assert hasattr(model, "user_id")
        assert hasattr(model, "session_id")
        assert hasattr(model, "search_query")
        assert hasattr(model, "search_type")
        assert hasattr(model, "search_filters")
        assert hasattr(model, "is_public")
        assert hasattr(model, "is_favorite")
        assert hasattr(model, "created_at")
        assert hasattr(model, "updated_at")
        assert hasattr(model, "last_used")
        assert hasattr(model, "use_count")


class TestUserPreference:
    """Test UserPreference model."""

    def test_table_name(self):
        """Test table name is correct."""
        assert UserPreference.__tablename__ == "user_preferences"

    def test_columns(self):
        """Test that required columns exist."""
        model = UserPreference
        assert hasattr(model, "id")
        assert hasattr(model, "user_id")
        assert hasattr(model, "session_id")
        assert hasattr(model, "preference_type")
        assert hasattr(model, "preference_key")
        assert hasattr(model, "preference_value")
        assert hasattr(model, "created_at")
        assert hasattr(model, "updated_at")

    def test_unique_constraint(self):
        """Test unique constraint on user preferences."""
        constraints = UserPreference.__table_args__
        assert len(constraints) == 1
        constraint = constraints[0]
        assert constraint.name == "uq_user_preference"


class TestSearchAnalytics:
    """Test SearchAnalytics model."""

    def test_table_name(self):
        """Test table name is correct."""
        assert SearchAnalytics.__tablename__ == "search_analytics"

    def test_columns(self):
        """Test that required columns exist."""
        model = SearchAnalytics
        assert hasattr(model, "id")
        assert hasattr(model, "search_id")
        assert hasattr(model, "user_id")
        assert hasattr(model, "session_id")
        assert hasattr(model, "query_text")
        assert hasattr(model, "query_hash")
        assert hasattr(model, "search_type")
        assert hasattr(model, "filters_applied")
        assert hasattr(model, "execution_time_ms")
        assert hasattr(model, "total_results")
        assert hasattr(model, "returned_results")
        assert hasattr(model, "has_results")
        assert hasattr(model, "timestamp")
        assert hasattr(model, "error_occurred")


class TestTranslationProject:
    """Test TranslationProject model."""

    def test_table_name(self):
        """Test table name is correct."""
        assert TranslationProject.__tablename__ == "translation_projects"

    def test_columns(self):
        """Test that required columns exist."""
        model = TranslationProject
        assert hasattr(model, "id")
        assert hasattr(model, "name")
        assert hasattr(model, "description")
        assert hasattr(model, "source_language")
        assert hasattr(model, "target_language")
        assert hasattr(model, "project_type")
        assert hasattr(model, "status")
        assert hasattr(model, "created_by")
        assert hasattr(model, "created_at")
        assert hasattr(model, "updated_at")

    def test_relationships(self):
        """Test that relationships are defined."""
        model = TranslationProject
        assert hasattr(model, "translation_memories")


class TestTranslationMemory:
    """Test TranslationMemory model."""

    def test_table_name(self):
        """Test table name is correct."""
        assert TranslationMemory.__tablename__ == "translation_memory"

    def test_columns(self):
        """Test that required columns exist."""
        model = TranslationMemory
        assert hasattr(model, "id")
        assert hasattr(model, "project_id")
        assert hasattr(model, "source_text")
        assert hasattr(model, "target_text")
        assert hasattr(model, "source_language")
        assert hasattr(model, "target_language")
        assert hasattr(model, "domain")
        assert hasattr(model, "subdomain")
        assert hasattr(model, "quality_score")
        assert hasattr(model, "confidence_score")
        assert hasattr(model, "usage_count")
        assert hasattr(model, "context_hash")
        assert hasattr(model, "tm_metadata")
        assert hasattr(model, "created_by")
        assert hasattr(model, "validated_by")

    def test_relationships(self):
        """Test that relationships are defined."""
        model = TranslationMemory
        assert hasattr(model, "project")
        assert hasattr(model, "embeddings")

    def test_foreign_key_cascade(self):
        """Test foreign key cascade behavior."""
        project_id_column = None
        for column in TranslationMemory.__table__.columns:
            if column.name == "project_id":
                project_id_column = column
                break

        assert project_id_column is not None
        assert len(project_id_column.foreign_keys) == 1
        fk = list(project_id_column.foreign_keys)[0]
        assert fk.ondelete == "CASCADE"


class TestTranslationEmbedding:
    """Test TranslationEmbedding model."""

    def test_table_name(self):
        """Test table name is correct."""
        assert TranslationEmbedding.__tablename__ == "translation_embeddings"

    def test_columns(self):
        """Test that required columns exist."""
        model = TranslationEmbedding
        assert hasattr(model, "id")
        assert hasattr(model, "memory_id")
        assert hasattr(model, "embedding")
        assert hasattr(model, "text_hash")
        assert hasattr(model, "created_at")

    def test_relationships(self):
        """Test that relationships are defined."""
        model = TranslationEmbedding
        assert hasattr(model, "memory")

    def test_foreign_key_cascade(self):
        """Test foreign key cascade behavior."""
        memory_id_column = None
        for column in TranslationEmbedding.__table__.columns:
            if column.name == "memory_id":
                memory_id_column = column
                break

        assert memory_id_column is not None
        assert len(memory_id_column.foreign_keys) == 1
        fk = list(memory_id_column.foreign_keys)[0]
        assert fk.ondelete == "CASCADE"


class TestModelDefaults:
    """Test model default values."""

    def test_job_description_defaults(self):
        """Test JobDescription default values."""
        # This would require actual SQLAlchemy session to test properly
        # For now, just check that defaults are set (SQLAlchemy func objects are not callable)
        assert JobDescription.processed_date.default is not None
        assert JobDescription.created_at.default is not None
        assert JobDescription.updated_at.default is not None

    def test_data_quality_metrics_defaults(self):
        """Test DataQualityMetrics default values."""
        assert DataQualityMetrics.processing_errors_count.default.arg == 0
        assert DataQualityMetrics.validation_errors_count.default.arg == 0

    def test_saved_search_defaults(self):
        """Test SavedSearch default values."""
        assert SavedSearch.search_type.default.arg == "text"
        assert SavedSearch.is_public.default.arg == "private"
        assert SavedSearch.is_favorite.default.arg == "false"
        assert SavedSearch.use_count.default.arg == 0

    def test_translation_project_defaults(self):
        """Test TranslationProject default values."""
        assert TranslationProject.project_type.default.arg == "job_descriptions"
        assert TranslationProject.status.default.arg == "active"

    def test_translation_memory_defaults(self):
        """Test TranslationMemory default values."""
        assert TranslationMemory.usage_count.default.arg == 0
        assert callable(TranslationMemory.tm_metadata.default.arg)  # dict() function


class TestColumnTypes:
    """Test column type definitions."""

    def test_decimal_columns(self):
        """Test DECIMAL column definitions."""
        # JobComparison
        overall_score = JobComparison.overall_score
        assert str(overall_score.type) == "DECIMAL(4, 3)"

        # DataQualityMetrics
        completeness_score = DataQualityMetrics.content_completeness_score
        assert str(completeness_score.type) == "DECIMAL(4, 3)"

        # AIUsageTracking
        cost_column = AIUsageTracking.cost_usd
        assert str(cost_column.type) == "DECIMAL(10, 6)"

    def test_string_column_lengths(self):
        """Test string column length definitions."""
        assert JobDescription.job_number.type.length == 20
        assert JobDescription.title.type.length == 500
        assert JobDescription.classification.type.length == 10
        assert JobDescription.language.type.length == 2
        assert JobDescription.file_path.type.length == 1000

    def test_text_columns(self):
        """Test TEXT column definitions."""
        assert str(JobDescription.raw_content.type) == "TEXT"
        assert str(JobSection.section_content.type) == "TEXT"
        assert str(ContentChunk.chunk_text.type) == "TEXT"

    def test_jsonb_columns(self):
        """Test JSONB column definitions."""
        assert str(JobComparison.section_scores.type) == "JSONB"
        assert str(DataQualityMetrics.validation_results.type) == "JSONB"
        assert str(SavedSearch.search_filters.type) == "JSONB"
        assert str(TranslationMemory.tm_metadata.type) == "JSONB"

    def test_vector_columns(self):
        """Test vector column definitions."""
        embedding_col = ContentChunk.embedding
        assert "VECTOR" in str(embedding_col.type)

    def test_array_columns(self):
        """Test array column definitions for translation embeddings."""
        embedding_col = TranslationEmbedding.embedding
        # This should be a PostgreSQL ARRAY type
        assert "ARRAY" in str(embedding_col.type) or hasattr(
            embedding_col.type, "item_type"
        )


class TestRelationships:
    """Test model relationships."""

    def test_job_description_relationships(self):
        """Test JobDescription relationship configurations."""
        # Test relationship properties exist
        assert hasattr(JobDescription.sections, "property")
        assert hasattr(JobDescription.metadata_entry, "property")
        assert hasattr(JobDescription.chunks, "property")

        # Test back_populates configuration
        sections_rel = JobDescription.sections.property
        assert sections_rel.back_populates == "job"

    def test_job_section_relationships(self):
        """Test JobSection relationship configurations."""
        job_rel = JobSection.job.property
        chunks_rel = JobSection.chunks.property

        assert job_rel.back_populates == "sections"
        assert chunks_rel.back_populates == "section"

    def test_translation_relationships(self):
        """Test translation model relationships."""
        # TranslationProject -> TranslationMemory
        tm_rel = TranslationProject.translation_memories.property
        assert tm_rel.back_populates == "project"

        # TranslationMemory -> TranslationProject
        proj_rel = TranslationMemory.project.property
        assert proj_rel.back_populates == "translation_memories"

        # TranslationMemory -> TranslationEmbedding
        emb_rel = TranslationMemory.embeddings.property
        assert emb_rel.back_populates == "memory"
