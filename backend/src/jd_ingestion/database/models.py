from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    DECIMAL,
    Date,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import VECTOR

Base = declarative_base()


class JobDescription(Base):
    __tablename__ = "job_descriptions"
    id = Column(Integer, primary_key=True)
    job_number = Column(String(20), unique=True)
    title = Column(String(500))
    classification = Column(String(10))
    language = Column(String(2))
    file_path = Column(String(1000))
    raw_content = Column(Text)
    processed_date = Column(DateTime, default=func.now())
    file_hash = Column(String(64))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    sections = relationship("JobSection", back_populates="job")
    metadata_entry = relationship("JobMetadata", back_populates="job", uselist=False)
    chunks = relationship("ContentChunk", back_populates="job")


class JobSection(Base):
    __tablename__ = "job_sections"
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("job_descriptions.id"))
    section_type = Column(String(50))
    section_content = Column(Text)
    section_order = Column(Integer)

    job = relationship("JobDescription", back_populates="sections")
    chunks = relationship("ContentChunk", back_populates="section")


class ContentChunk(Base):
    __tablename__ = "content_chunks"
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("job_descriptions.id"))
    section_id = Column(Integer, ForeignKey("job_sections.id"))
    chunk_text = Column(Text)
    chunk_index = Column(Integer)
    embedding = Column(VECTOR(1536))  # OpenAI embedding dimension

    job = relationship("JobDescription", back_populates="chunks")
    section = relationship("JobSection", back_populates="chunks")


class JobMetadata(Base):
    __tablename__ = "job_metadata"
    id = Column(Integer, primary_key=True)  # Added primary key for JobMetadata
    job_id = Column(Integer, ForeignKey("job_descriptions.id"))
    reports_to = Column(String(500))
    department = Column(String(200))
    location = Column(String(200))
    fte_count = Column(Integer)
    salary_budget = Column(DECIMAL)
    effective_date = Column(Date)

    job = relationship("JobDescription", back_populates="metadata_entry")


class JobComparison(Base):
    __tablename__ = "job_comparisons"

    id = Column(Integer, primary_key=True)
    job_a_id = Column(Integer, ForeignKey("job_descriptions.id"))
    job_b_id = Column(Integer, ForeignKey("job_descriptions.id"))
    comparison_type = Column(String(50))  # 'similarity', 'skill_gap', 'career_path'
    overall_score = Column(DECIMAL(4, 3))
    section_scores = Column(JSONB)  # detailed scores by section
    metadata_comparison = Column(JSONB)  # salary, level, dept differences
    skills_analysis = Column(JSONB)  # extracted skills comparison
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint(
            "job_a_id", "job_b_id", "comparison_type", name="uq_job_comparison"
        ),
    )

    job_a = relationship("JobDescription", foreign_keys=[job_a_id])
    job_b = relationship("JobDescription", foreign_keys=[job_b_id])


class JobSkill(Base):
    __tablename__ = "job_skills"

    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("job_descriptions.id"))
    skill_category = Column(String(100))  # 'technical', 'leadership', 'communication'
    skill_name = Column(String(200))
    skill_level = Column(String(50))  # 'required', 'preferred', 'asset'
    confidence_score = Column(DECIMAL(4, 3))
    extracted_from_section = Column(String(50))
    created_at = Column(DateTime, default=func.now())

    job = relationship("JobDescription")


class CareerPath(Base):
    __tablename__ = "career_paths"

    id = Column(Integer, primary_key=True)
    from_job_id = Column(Integer, ForeignKey("job_descriptions.id"))
    to_job_id = Column(Integer, ForeignKey("job_descriptions.id"))
    progression_type = Column(String(50))  # 'vertical', 'lateral', 'diagonal'
    feasibility_score = Column(DECIMAL(4, 3))
    skill_gap_analysis = Column(JSONB)
    required_experience_years = Column(Integer)
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint("from_job_id", "to_job_id", name="uq_career_path"),
    )

    from_job = relationship("JobDescription", foreign_keys=[from_job_id])
    to_job = relationship("JobDescription", foreign_keys=[to_job_id])


class ClassificationBenchmark(Base):
    __tablename__ = "classification_benchmarks"

    id = Column(Integer, primary_key=True)
    classification = Column(String(10))
    department = Column(String(200))
    avg_salary = Column(DECIMAL)
    median_salary = Column(DECIMAL)
    avg_fte_supervised = Column(Integer)
    common_skills = Column(JSONB)
    typical_reports_to = Column(String(500))
    job_count = Column(Integer)
    last_updated = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint(
            "classification", "department", name="uq_classification_benchmark"
        ),
    )


class DataQualityMetrics(Base):
    __tablename__ = "data_quality_metrics"

    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("job_descriptions.id"), unique=True)

    # Content completeness scores (0.0 - 1.0)
    content_completeness_score = Column(DECIMAL(4, 3))
    sections_completeness_score = Column(DECIMAL(4, 3))
    metadata_completeness_score = Column(DECIMAL(4, 3))

    # Content quality indicators
    has_structured_fields = Column(String(10))  # 'complete', 'partial', 'missing'
    has_all_sections = Column(String(10))  # 'complete', 'partial', 'missing'
    has_embeddings = Column(String(10))  # 'complete', 'partial', 'missing'

    # Processing quality metrics
    processing_errors_count = Column(Integer, default=0)
    validation_errors_count = Column(Integer, default=0)
    content_extraction_success = Column(String(10))  # 'success', 'partial', 'failed'

    # Content characteristics
    raw_content_length = Column(Integer)
    processed_content_length = Column(Integer)
    sections_extracted_count = Column(Integer)
    chunks_generated_count = Column(Integer)

    # Language and encoding quality
    language_detection_confidence = Column(DECIMAL(4, 3))
    encoding_issues_detected = Column(String(10))  # 'none', 'minor', 'major'

    # Detailed validation results
    validation_results = Column(JSONB)  # Specific validation error details
    quality_flags = Column(JSONB)  # Quality indicators and warnings

    # Scoring metadata
    last_calculated = Column(DateTime, default=func.now())
    calculation_version = Column(String(20), default="1.0")

    job = relationship("JobDescription")


class AIUsageTracking(Base):
    __tablename__ = "ai_usage_tracking"

    id = Column(Integer, primary_key=True)
    request_timestamp = Column(DateTime, default=func.now())
    service_type = Column(String(50))  # 'openai', 'anthropic', etc.
    operation_type = Column(String(50))  # 'embedding', 'completion', 'classification'
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    total_tokens = Column(Integer)
    cost_usd = Column(DECIMAL(10, 6))
    request_id = Column(String(100))
    model_name = Column(String(100))
    success = Column(String(10))  # 'success', 'error', 'timeout'
    error_message = Column(Text)
    request_metadata = Column(JSONB)


class UsageAnalytics(Base):
    __tablename__ = "usage_analytics"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=func.now())

    # User and session tracking
    session_id = Column(String(100))
    user_id = Column(String(100))  # For future user authentication
    ip_address = Column(String(45))
    user_agent = Column(String(500))

    # Activity tracking
    action_type = Column(String(50))  # 'search', 'upload', 'export', 'view', 'analyze'
    endpoint = Column(String(200))
    http_method = Column(String(10))
    resource_id = Column(String(100))  # job_id, search_id, etc.

    # Performance metrics
    response_time_ms = Column(Integer)
    status_code = Column(Integer)

    # Search-specific tracking
    search_query = Column(Text)
    search_filters = Column(JSONB)
    results_count = Column(Integer)

    # Processing metrics
    processing_time_ms = Column(Integer)
    files_processed = Column(Integer)

    # Additional context
    request_metadata = Column(JSONB)


class SystemMetrics(Base):
    __tablename__ = "system_metrics"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=func.now())
    metric_type = Column(String(50))  # 'daily', 'hourly', 'weekly', 'monthly'

    # Aggregated usage stats
    total_requests = Column(Integer, default=0)
    unique_sessions = Column(Integer, default=0)
    total_searches = Column(Integer, default=0)
    total_uploads = Column(Integer, default=0)
    total_exports = Column(Integer, default=0)

    # Performance stats
    avg_response_time_ms = Column(Integer)
    error_rate = Column(DECIMAL(5, 4))  # Percentage as decimal

    # AI usage stats
    total_ai_requests = Column(Integer, default=0)
    total_tokens_used = Column(Integer, default=0)
    total_ai_cost_usd = Column(DECIMAL(12, 6), default=0)

    # Storage and processing stats
    total_jobs_processed = Column(Integer, default=0)
    total_embeddings_generated = Column(Integer, default=0)
    storage_size_bytes = Column(Integer, default=0)

    # Quality metrics
    avg_data_quality_score = Column(DECIMAL(4, 3))

    # Period definition
    period_start = Column(DateTime)
    period_end = Column(DateTime)

    # Additional metrics
    detailed_metrics = Column(JSONB)


class SavedSearch(Base):
    __tablename__ = "saved_searches"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # User identification (for future user authentication)
    user_id = Column(String(100))  # Optional for now
    session_id = Column(String(100))  # Fallback for anonymous users

    # Search parameters
    search_query = Column(Text)
    search_type = Column(String(50), default="text")  # 'text', 'vector', 'hybrid'
    search_filters = Column(JSONB)  # Filter criteria (classification, language, etc.)

    # Search configuration
    is_public = Column(String(10), default="private")  # 'public', 'private'
    is_favorite = Column(String(10), default="false")  # 'true', 'false'

    # Usage tracking
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_used = Column(DateTime, default=func.now())
    use_count = Column(Integer, default=0)

    # Search results metadata
    last_result_count = Column(Integer)
    last_execution_time_ms = Column(Integer)

    # Additional configuration
    search_metadata = Column(JSONB)  # Store additional search settings


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(100))  # Optional for now
    session_id = Column(String(100))  # Fallback for anonymous users

    # Preference categories
    preference_type = Column(String(50))  # 'ui', 'search', 'export', 'display'
    preference_key = Column(String(100))
    preference_value = Column(JSONB)

    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "session_id",
            "preference_type",
            "preference_key",
            name="uq_user_preference",
        ),
    )


class SearchAnalytics(Base):
    __tablename__ = "search_analytics"

    id = Column(Integer, primary_key=True)

    # Search identification
    search_id = Column(String(100))  # Unique identifier for search session
    user_id = Column(String(100))  # Optional user identifier
    session_id = Column(String(100))  # Session identifier
    ip_address = Column(String(45))  # User's IP address

    # Query information
    query_text = Column(Text)  # Original search query
    query_hash = Column(String(64))  # Hash of query for deduplication
    search_type = Column(String(20))  # 'semantic', 'fulltext', 'hybrid'

    # Filters applied
    filters_applied = Column(JSONB)  # JSON of all filters used

    # Performance metrics
    execution_time_ms = Column(Integer)  # Query execution time
    total_response_time_ms = Column(Integer)  # Total API response time
    embedding_time_ms = Column(Integer)  # Time to generate embeddings (if semantic)

    # Result metrics
    total_results = Column(Integer)  # Total number of results found
    returned_results = Column(Integer)  # Number of results returned to user
    has_results = Column(String(10))  # 'yes', 'no', 'error'

    # Result relevance (user feedback)
    clicked_results = Column(JSONB)  # Array of clicked result IDs
    result_rankings = Column(JSONB)  # User interaction with result order
    user_satisfaction = Column(Integer)  # 1-5 rating if provided

    # System context
    timestamp = Column(DateTime, default=func.now())
    api_version = Column(String(10))  # API version used
    client_type = Column(String(20))  # 'web', 'api', 'mobile', etc.

    # Error tracking
    error_occurred = Column(String(10), default="no")  # 'yes', 'no'
    error_type = Column(String(50))  # Type of error if any
    error_message = Column(Text)  # Error details


# Phase 2 Models: Translation Memory System
class TranslationProject(Base):
    __tablename__ = "translation_projects"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    source_language = Column(String(5), nullable=False)
    target_language = Column(String(5), nullable=False)
    project_type = Column(String(50), default='job_descriptions')
    status = Column(String(20), default='active')
    created_by = Column(Integer)  # References users table when implemented
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    translation_memories = relationship("TranslationMemory", back_populates="project")


class TranslationMemory(Base):
    __tablename__ = "translation_memory"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('translation_projects.id', ondelete='CASCADE'))
    source_text = Column(Text, nullable=False)
    target_text = Column(Text, nullable=False)
    source_language = Column(String(5), nullable=False)
    target_language = Column(String(5), nullable=False)
    domain = Column(String(50))  # 'government', 'hr', 'technical'
    subdomain = Column(String(50))  # 'job_descriptions', 'policies'
    quality_score = Column(DECIMAL(3, 2))
    confidence_score = Column(DECIMAL(3, 2))
    usage_count = Column(Integer, default=0)
    context_hash = Column(String(64))
    tm_metadata = Column(JSONB, default=dict)
    created_by = Column(Integer)  # References users table
    validated_by = Column(Integer)  # References users table
    created_at = Column(DateTime, default=func.now())
    last_used = Column(DateTime)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    project = relationship("TranslationProject", back_populates="translation_memories")
    embeddings = relationship("TranslationEmbedding", back_populates="memory")


class TranslationEmbedding(Base):
    __tablename__ = "translation_embeddings"

    id = Column(Integer, primary_key=True)
    memory_id = Column(Integer, ForeignKey('translation_memory.id', ondelete='CASCADE'))
    embedding = Column(postgresql.ARRAY(postgresql.REAL))  # pgvector will handle this
    text_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    memory = relationship("TranslationMemory", back_populates="embeddings")
