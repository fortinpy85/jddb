# backend/src/jd_ingestion/database/models.py

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    ForeignKey,
    JSON,
    Text,
    Date,
    DECIMAL,
)
from sqlalchemy.orm import relationship, DeclarativeBase
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
from datetime import datetime


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    role = Column(String, default="user", nullable=False)
    department = Column(String, nullable=True)
    security_clearance = Column(String, nullable=True)
    preferred_language = Column(String, default="en", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow, nullable=True)

    sessions = relationship("UserSession", back_populates="user")
    permissions = relationship("UserPermission", back_populates="user")


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_token = Column(String, unique=True, index=True, nullable=False)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_activity = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="sessions")


class UserPermission(Base):
    __tablename__ = "user_permissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    resource_type = Column(String, nullable=False)
    resource_id = Column(Integer, nullable=True)
    permission_type = Column(String, nullable=False)
    granted_by = Column(Integer, nullable=True)
    granted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="permissions")


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        String, nullable=True
    )  # Allow string IDs to match SavedSearch pattern
    session_id = Column(
        String, nullable=True
    )  # Add session_id for session-based preferences
    preference_type = Column(
        String, nullable=False
    )  # Add preference type (ui, search, etc.)
    preference_key = Column(String, nullable=False)
    preference_value = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow, nullable=True)


class SavedSearch(Base):
    __tablename__ = "saved_searches"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(String, nullable=True)
    session_id = Column(String, nullable=True)
    search_query = Column(Text, nullable=True)
    search_type = Column(String, default="general", nullable=False)
    search_filters = Column(JSONB, nullable=True)
    is_public = Column(String, default="false", nullable=False)
    is_favorite = Column(String, default="false", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow, nullable=True)
    last_used = Column(DateTime, nullable=True)
    use_count = Column(Integer, default=0, nullable=False)
    last_result_count = Column(Integer, nullable=True)
    last_execution_time_ms = Column(Integer, nullable=True)
    search_metadata = Column(JSONB, nullable=True)


# Core job description models
class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(Integer, primary_key=True, index=True)
    job_number = Column(String(20), unique=True, index=True, nullable=True)
    title = Column(String(500), nullable=True)
    classification = Column(String(10), nullable=True)
    language = Column(String(2), nullable=True)
    file_path = Column(String(1000), nullable=True)
    raw_content = Column(Text, nullable=True)
    processed_date = Column(DateTime, default=datetime.utcnow, nullable=True)
    file_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow, nullable=True)

    # Relationships
    sections = relationship("JobSection", back_populates="job")
    chunks = relationship("ContentChunk", back_populates="job")
    job_metadata = relationship("JobMetadata", back_populates="job", uselist=False)
    quality_metrics = relationship(
        "DataQualityMetrics", back_populates="job", uselist=False
    )


class JobSection(Base):
    __tablename__ = "job_sections"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_descriptions.id"), nullable=False)
    section_type = Column(String(50), nullable=True)
    section_content = Column(Text, nullable=True)
    section_order = Column(Integer, nullable=True)

    # Relationships
    job = relationship("JobDescription", back_populates="sections")
    chunks = relationship("ContentChunk", back_populates="section")


class JobMetadata(Base):
    __tablename__ = "job_metadata"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_descriptions.id"), nullable=False)
    reports_to = Column(String(500), nullable=True)
    department = Column(String(200), nullable=True)
    location = Column(String(200), nullable=True)
    fte_count = Column(Integer, nullable=True)
    salary_budget = Column(DECIMAL, nullable=True)
    effective_date = Column(Date, nullable=True)

    # Relationships
    job = relationship("JobDescription", back_populates="job_metadata")


class ContentChunk(Base):
    __tablename__ = "content_chunks"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_descriptions.id"), nullable=False)
    section_id = Column(Integer, ForeignKey("job_sections.id"), nullable=True)
    chunk_text = Column(Text, nullable=True)
    chunk_index = Column(Integer, nullable=True)
    embedding = Column(Vector(1536), nullable=True)

    # Relationships
    job = relationship("JobDescription", back_populates="chunks")
    section = relationship("JobSection", back_populates="chunks")


# Analytics and quality models
class SearchAnalytics(Base):
    __tablename__ = "search_analytics"

    id = Column(Integer, primary_key=True, index=True)
    search_id = Column(String(100), nullable=True)
    user_id = Column(String(100), nullable=True)
    session_id = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    query_text = Column(Text, nullable=True)
    query_hash = Column(String(64), nullable=True)
    search_type = Column(String(20), nullable=True)
    filters_applied = Column(JSONB, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    total_response_time_ms = Column(Integer, nullable=True)
    embedding_time_ms = Column(Integer, nullable=True)
    total_results = Column(Integer, nullable=True)
    returned_results = Column(Integer, nullable=True)
    has_results = Column(String(10), nullable=True)
    clicked_results = Column(JSONB, nullable=True)
    result_rankings = Column(JSONB, nullable=True)
    user_satisfaction = Column(Integer, nullable=True)
    timestamp = Column(DateTime, nullable=True)
    api_version = Column(String(10), nullable=True)
    client_type = Column(String(20), nullable=True)
    error_occurred = Column(String(10), nullable=True)
    error_type = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)


class DataQualityMetrics(Base):
    __tablename__ = "data_quality_metrics"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_descriptions.id"), nullable=False)
    content_completeness_score = Column(DECIMAL(4, 3), nullable=True)
    sections_completeness_score = Column(DECIMAL(4, 3), nullable=True)
    metadata_completeness_score = Column(DECIMAL(4, 3), nullable=True)
    has_structured_fields = Column(String(10), nullable=True)
    has_all_sections = Column(String(10), nullable=True)
    has_embeddings = Column(String(10), nullable=True)
    processing_errors_count = Column(Integer, nullable=True)
    validation_errors_count = Column(Integer, nullable=True)
    content_extraction_success = Column(String(10), nullable=True)
    raw_content_length = Column(Integer, nullable=True)
    processed_content_length = Column(Integer, nullable=True)
    sections_extracted_count = Column(Integer, nullable=True)
    chunks_generated_count = Column(Integer, nullable=True)
    language_detection_confidence = Column(DECIMAL(4, 3), nullable=True)
    encoding_issues_detected = Column(String(10), nullable=True)
    validation_results = Column(JSONB, nullable=True)
    quality_flags = Column(JSONB, nullable=True)
    last_calculated = Column(DateTime, nullable=True)
    calculation_version = Column(String(20), nullable=True)

    # Relationships
    job = relationship("JobDescription", back_populates="quality_metrics")


# Job analysis models
class JobComparison(Base):
    __tablename__ = "job_comparisons"

    id = Column(Integer, primary_key=True, index=True)
    job1_id = Column(Integer, ForeignKey("job_descriptions.id"), nullable=False)
    job2_id = Column(Integer, ForeignKey("job_descriptions.id"), nullable=False)
    comparison_type = Column(String(50), nullable=True)
    similarity_score = Column(DECIMAL(4, 3), nullable=True)
    differences = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    job1 = relationship("JobDescription", foreign_keys=[job1_id])
    job2 = relationship("JobDescription", foreign_keys=[job2_id])


class JobSkill(Base):
    __tablename__ = "job_skills"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_descriptions.id"), nullable=False)
    skill_name = Column(String(200), nullable=False)
    skill_category = Column(String(100), nullable=True)
    proficiency_level = Column(String(50), nullable=True)
    is_required = Column(Boolean, default=False, nullable=False)
    extracted_context = Column(Text, nullable=True)
    confidence_score = Column(DECIMAL(4, 3), nullable=True)

    # Relationships
    job = relationship("JobDescription")


# Additional analytics models
class UsageAnalytics(Base):
    __tablename__ = "usage_analytics"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=True)
    session_id = Column(String(100), nullable=True)
    user_id = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    action_type = Column(String(50), nullable=True)
    endpoint = Column(String(200), nullable=True)
    http_method = Column(String(10), nullable=True)
    resource_id = Column(String(100), nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    status_code = Column(Integer, nullable=True)
    search_query = Column(Text, nullable=True)
    search_filters = Column(JSONB, nullable=True)
    results_count = Column(Integer, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    files_processed = Column(Integer, nullable=True)
    request_metadata = Column(JSONB, nullable=True)


class SystemMetrics(Base):
    __tablename__ = "system_metrics"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=True)
    metric_type = Column(String(50), nullable=True)
    total_requests = Column(Integer, nullable=True)
    unique_sessions = Column(Integer, nullable=True)
    total_searches = Column(Integer, nullable=True)
    total_uploads = Column(Integer, nullable=True)
    total_exports = Column(Integer, nullable=True)
    avg_response_time_ms = Column(Integer, nullable=True)
    error_rate = Column(DECIMAL(5, 4), nullable=True)
    total_ai_requests = Column(Integer, nullable=True)
    total_tokens_used = Column(Integer, nullable=True)
    total_ai_cost_usd = Column(DECIMAL(12, 6), nullable=True)
    total_jobs_processed = Column(Integer, nullable=True)
    total_embeddings_generated = Column(Integer, nullable=True)
    storage_size_bytes = Column(Integer, nullable=True)
    avg_data_quality_score = Column(DECIMAL(4, 3), nullable=True)
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    detailed_metrics = Column(JSONB, nullable=True)


class AIUsageTracking(Base):
    __tablename__ = "ai_usage_tracking"

    id = Column(Integer, primary_key=True, index=True)
    request_timestamp = Column(DateTime, nullable=True)
    service_type = Column(String(50), nullable=True)
    operation_type = Column(String(50), nullable=True)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    cost_usd = Column(DECIMAL(10, 6), nullable=True)
    request_id = Column(String(100), nullable=True)
    model_name = Column(String(100), nullable=True)
    success = Column(String(10), nullable=True)
    error_message = Column(Text, nullable=True)
    request_metadata = Column(JSONB, nullable=True)
