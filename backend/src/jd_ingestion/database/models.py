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
    Table,
    Float,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, DeclarativeBase, synonym
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import TypeDecorator
from pgvector.sqlalchemy import Vector
from datetime import datetime
from passlib.context import CryptContext

# Password hashing configuration
# Configure bcrypt with compatibility for bcrypt 5.x
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__ident="2b",  # Use bcrypt $2b$ variant
    bcrypt__min_rounds=12,  # Set reasonable cost factor
)


# Type adapter that uses JSONB for PostgreSQL, JSON for other databases (like SQLite)
class JSONBType(TypeDecorator):
    """
    Platform-agnostic JSON/JSONB type.

    Uses JSONB for PostgreSQL for better performance and indexing.
    Falls back to JSON for other databases like SQLite.
    """

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(JSON())

    def __repr__(self):
        return "JSONB"

    def __str__(self):
        return "JSONB"


class Base(DeclarativeBase):
    pass


# Association table for many-to-many relationship between JobDescription and Skill
job_description_skills = Table(
    "job_description_skills",
    Base.metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column(
        "job_id",
        Integer,
        ForeignKey("job_descriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column(
        "skill_id",
        Integer,
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column(
        "confidence", Float, nullable=True
    ),  # Confidence score from Lightcast extraction
    Column("created_at", DateTime, default=datetime.utcnow, nullable=False),
)


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

    def set_password(self, password: str) -> None:
        """Hash and set the password."""
        # Bcrypt has a maximum password length of 72 bytes
        # Truncate password to ensure it's within bcrypt limits
        if len(password.encode("utf-8")) > 72:
            password = password.encode("utf-8")[:72].decode("utf-8", errors="ignore")
        self.password_hash = pwd_context.hash(password)  # type: ignore[assignment]

    def verify_password(self, password: str) -> bool:
        """Verify a password against the hash."""
        return bool(pwd_context.verify(password, self.password_hash))  # type: ignore[arg-type]

    def update_last_login(self) -> None:
        """Update the last login timestamp."""
        self.last_login = datetime.utcnow()  # type: ignore[assignment]


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

    __table_args__ = (
        UniqueConstraint(
            "user_id", "preference_type", "preference_key", name="uq_user_preference"
        ),
    )


class SavedSearch(Base):
    __tablename__ = "saved_searches"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(String, nullable=True)
    session_id = Column(String, nullable=True)
    search_query = Column(Text, nullable=True)
    search_type = Column(String, default="text", nullable=False)
    search_filters = Column(JSONBType, nullable=True)
    is_public = Column(String, default="private", nullable=False)
    is_favorite = Column(String, default="false", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow, nullable=True)
    last_used = Column(DateTime, nullable=True)
    use_count = Column(Integer, default=0, nullable=False)
    last_result_count = Column(Integer, nullable=True)
    last_execution_time_ms = Column(Integer, nullable=True)
    search_metadata = Column(JSONBType, nullable=True)


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
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True
    )

    # Relationships with CASCADE delete-orphan for proper ORM-level deletion handling
    sections = relationship(
        "JobSection", back_populates="job", cascade="all, delete-orphan"
    )
    chunks = relationship(
        "ContentChunk", back_populates="job", cascade="all, delete-orphan"
    )
    job_metadata = relationship(
        "JobMetadata", back_populates="job", uselist=False, cascade="all, delete-orphan"
    )
    # Synonym for backward compatibility - tests expect 'metadata_entry'
    metadata_entry = synonym("job_metadata")
    quality_metrics = relationship(
        "DataQualityMetrics",
        back_populates="job",
        uselist=False,
        cascade="all, delete-orphan",
    )
    skills = relationship(
        "Skill",
        secondary=job_description_skills,
        back_populates="job_descriptions",
        lazy="selectin",
    )


class JobSection(Base):
    __tablename__ = "job_sections"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(
        Integer, ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False
    )
    section_type = Column(String(50), nullable=True)
    section_content = Column(Text, nullable=True)
    section_order = Column(Integer, nullable=True)

    # Relationships
    job = relationship("JobDescription", back_populates="sections")
    chunks = relationship("ContentChunk", back_populates="section")


class JobMetadata(Base):
    __tablename__ = "job_metadata"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(
        Integer, ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False
    )
    reports_to = Column(String(500), nullable=True)
    department = Column(String(200), nullable=True)
    location = Column(String(200), nullable=True)
    fte_count = Column(Integer, nullable=True)
    salary_budget = Column(Float, nullable=True)  # Use Float for SQLite compatibility
    effective_date = Column(Date, nullable=True)

    # Relationships
    job = relationship("JobDescription", back_populates="job_metadata")


class ContentChunk(Base):
    __tablename__ = "content_chunks"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(
        Integer, ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False
    )
    section_id = Column(
        Integer, ForeignKey("job_sections.id", ondelete="CASCADE"), nullable=True
    )
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
    filters_applied = Column(JSONBType, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    total_response_time_ms = Column(Integer, nullable=True)
    embedding_time_ms = Column(Integer, nullable=True)
    total_results = Column(Integer, nullable=True)
    returned_results = Column(Integer, nullable=True)
    has_results = Column(String(10), nullable=True)
    clicked_results = Column(JSONBType, nullable=True)
    result_rankings = Column(JSONBType, nullable=True)
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
    job_id = Column(
        Integer,
        ForeignKey("job_descriptions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    content_completeness_score: float = Column(DECIMAL(4, 3), nullable=True)  # type: ignore[assignment]
    sections_completeness_score: float = Column(DECIMAL(4, 3), nullable=True)  # type: ignore[assignment]
    metadata_completeness_score: float = Column(DECIMAL(4, 3), nullable=True)  # type: ignore[assignment]
    has_structured_fields = Column(String(10), nullable=True)
    has_all_sections = Column(String(10), nullable=True)
    has_embeddings = Column(String(10), nullable=True)
    processing_errors_count = Column(Integer, default=0, nullable=True)
    validation_errors_count = Column(Integer, default=0, nullable=True)
    content_extraction_success = Column(String(10), nullable=True)
    raw_content_length = Column(Integer, nullable=True)
    processed_content_length = Column(Integer, nullable=True)
    sections_extracted_count = Column(Integer, nullable=True)
    chunks_generated_count = Column(Integer, nullable=True)
    language_detection_confidence: float = Column(DECIMAL(4, 3), nullable=True)  # type: ignore[assignment]
    encoding_issues_detected = Column(String(10), nullable=True)
    validation_results = Column(JSONBType, nullable=True)
    quality_flags = Column(JSONBType, nullable=True)
    last_calculated = Column(DateTime, nullable=True)
    calculation_version = Column(String(20), nullable=True)

    # Relationships
    job = relationship("JobDescription", back_populates="quality_metrics")


# Job analysis models
class JobComparison(Base):
    __tablename__ = "job_comparisons"

    id = Column(Integer, primary_key=True, index=True)
    job1_id = Column(
        Integer, ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False
    )
    job2_id = Column(
        Integer, ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False
    )
    comparison_type = Column(String(50), nullable=True)
    similarity_score: float = Column(DECIMAL(4, 3), nullable=True)  # type: ignore[assignment]
    overall_score: float = Column(DECIMAL(4, 3), nullable=True)  # type: ignore[assignment]
    section_scores = Column(JSONBType, nullable=True)
    differences = Column(JSONBType, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    job1 = relationship("JobDescription", foreign_keys=[job1_id])
    job2 = relationship("JobDescription", foreign_keys=[job2_id])


class Skill(Base):
    """
    Lightcast Skills - Standardized skills from Lightcast Open Skills taxonomy.

    This table stores skills extracted from job descriptions using the Lightcast API.
    Each skill is uniquely identified by its Lightcast ID and can be associated with
    multiple job descriptions through the job_description_skills association table.
    """

    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    lightcast_id = Column(
        String(50), unique=True, index=True, nullable=False
    )  # Lightcast skill ID (e.g., "KS123ABC")
    name = Column(String(500), nullable=False, index=True)  # Skill name
    skill_type = Column(
        String(100), nullable=True, index=True
    )  # Skill type/category from Lightcast
    description = Column(Text, nullable=True)  # Skill description
    category = Column(String(200), nullable=True)  # Additional categorization
    subcategory = Column(String(200), nullable=True)
    skill_metadata = Column(JSONBType, nullable=True)  # Additional Lightcast metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow, nullable=True)

    # Relationships
    job_descriptions = relationship(
        "JobDescription",
        secondary=job_description_skills,
        back_populates="skills",
        lazy="selectin",
    )


class JobSkill(Base):
    """
    DEPRECATED: Legacy job skills model.

    Use the Skill model and job_description_skills association table instead.
    This model is kept for backwards compatibility and may be removed in a future version.
    """

    __tablename__ = "job_skills"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(
        Integer, ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False
    )
    skill_name = Column(String(200), nullable=False)
    skill_category = Column(String(100), nullable=True)
    proficiency_level = Column(String(50), nullable=True)
    is_required = Column(Boolean, default=False, nullable=False)
    extracted_context = Column(Text, nullable=True)
    confidence_score: float = Column(DECIMAL(4, 3), nullable=True)  # type: ignore[assignment]

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
    search_filters = Column(JSONBType, nullable=True)
    results_count = Column(Integer, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    files_processed = Column(Integer, nullable=True)
    request_metadata = Column(JSONBType, nullable=True)


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
    error_rate: float = Column(DECIMAL(5, 4), nullable=True)  # type: ignore[assignment]
    total_ai_requests = Column(Integer, nullable=True)
    total_tokens_used = Column(Integer, nullable=True)
    total_ai_cost_usd: float = Column(DECIMAL(12, 6), nullable=True)  # type: ignore[assignment]
    total_jobs_processed = Column(Integer, nullable=True)
    total_embeddings_generated = Column(Integer, nullable=True)
    storage_size_bytes = Column(Integer, nullable=True)
    avg_data_quality_score: float = Column(DECIMAL(4, 3), nullable=True)  # type: ignore[assignment]
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    detailed_metrics = Column(JSONBType, nullable=True)


class AIUsageTracking(Base):
    __tablename__ = "ai_usage_tracking"

    id = Column(Integer, primary_key=True, index=True)
    request_timestamp = Column(DateTime, nullable=True)
    service_type = Column(String(50), nullable=True)
    operation_type = Column(String(50), nullable=True)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    cost_usd: float = Column(DECIMAL(10, 6), nullable=True)  # type: ignore[assignment]
    request_id = Column(String(100), nullable=True)
    model_name = Column(String(100), nullable=True)
    success = Column(String(10), nullable=True)
    error_message = Column(Text, nullable=True)
    request_metadata = Column(JSONBType, nullable=True)


class RLHFFeedback(Base):
    """
    RLHF (Reinforcement Learning from Human Feedback) Feedback

    Captures user feedback on AI suggestions to improve model performance.
    Tracks accept/reject decisions, modifications, and user preferences.
    """

    __tablename__ = "rlhf_feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    job_id = Column(
        Integer,
        ForeignKey("job_descriptions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    event_type = Column(
        String(50), nullable=False, index=True
    )  # accept, reject, modify, generate
    original_text = Column(Text, nullable=False)
    suggested_text = Column(Text, nullable=True)
    final_text = Column(Text, nullable=True)
    suggestion_type = Column(
        String(50), nullable=True, index=True
    )  # grammar, style, clarity, bias, compliance
    user_action = Column(
        String(50), nullable=False, index=True
    )  # accepted, rejected, modified
    confidence = Column(Float, nullable=True)  # AI confidence score (0.000-1.000)
    feedback_metadata = Column(
        JSONBType, nullable=True
    )  # Additional context (renamed from 'metadata' to avoid SQLAlchemy reserved name)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    job = relationship("JobDescription", foreign_keys=[job_id])


# Translation Memory models for Phase 2 collaborative features
class TranslationProject(Base):
    """
    Translation Project - Groups related translation memory entries.

    Organizes translations by project for better management and context.
    """

    __tablename__ = "translation_projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    source_language = Column(String(10), nullable=False, index=True)
    target_language = Column(String(10), nullable=False, index=True)
    project_type = Column(String(50), default="job_descriptions", nullable=False)
    status = Column(String(20), default="active", nullable=False, index=True)
    created_by = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow, nullable=True)

    # Relationships
    translations = relationship(
        "TranslationMemory", back_populates="project", cascade="all, delete-orphan"
    )
    creator = relationship("User", foreign_keys=[created_by])


class TranslationMemory(Base):
    """
    Translation Memory - Stores source-target translation pairs with metadata.

    Enables reuse of previously translated content with semantic similarity search.
    """

    __tablename__ = "translation_memory"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(
        Integer,
        ForeignKey("translation_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_text = Column(Text, nullable=False)
    target_text = Column(Text, nullable=False)
    source_language = Column(String(10), nullable=False, index=True)
    target_language = Column(String(10), nullable=False, index=True)
    domain = Column(String(100), nullable=True, index=True)
    subdomain = Column(String(100), nullable=True)
    quality_score: float = Column(DECIMAL(4, 3), nullable=True)  # type: ignore[assignment]
    confidence_score: float = Column(DECIMAL(4, 3), nullable=True)  # type: ignore[assignment]
    usage_count = Column(Integer, default=0, nullable=False)
    last_used = Column(DateTime, nullable=True)
    translation_metadata = Column(JSONBType, nullable=True)
    created_by = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow, nullable=True)

    # Relationships
    project = relationship("TranslationProject", back_populates="translations")
    embeddings = relationship(
        "TranslationEmbedding",
        back_populates="translation",
        cascade="all, delete-orphan",
    )
    creator = relationship("User", foreign_keys=[created_by])


class TranslationEmbedding(Base):
    """
    Translation Embedding - Stores vector embeddings for semantic similarity search.

    Uses pgvector for efficient similarity matching across translation memory.
    """

    __tablename__ = "translation_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    translation_id = Column(
        Integer,
        ForeignKey("translation_memory.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    embedding = Column(Vector(1536), nullable=False)
    embedding_model = Column(
        String(100), default="text-embedding-ada-002", nullable=False
    )
    text_hash = Column(String(64), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    translation = relationship("TranslationMemory", back_populates="embeddings")
