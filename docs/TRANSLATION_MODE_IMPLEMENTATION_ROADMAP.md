# Bilingual Translation Mode - Implementation Roadmap

## Overview

Comprehensive implementation plan for English↔French job description translation with translation memory, terminology management, and sentence-level concurrence validation.

**Implementation Date**: TBD (after job descriptions are properly ingested)
**Estimated Effort**: 6-8 weeks
**Priority**: High (Phase 7)
**Dependencies**: AI Improvement Mode infrastructure

---

## Phase 1: Database and Translation Memory Infrastructure (Week 1-2)

### 1.1 Database Schema Extensions

#### New Tables

**`translation_memory`**
```sql
CREATE TABLE translation_memory (
    id SERIAL PRIMARY KEY,
    source_language VARCHAR(5) NOT NULL CHECK (source_language IN ('en', 'fr')),
    target_language VARCHAR(5) NOT NULL CHECK (target_language IN ('en', 'fr')),
    source_text TEXT NOT NULL,
    target_text TEXT NOT NULL,
    section_type VARCHAR(100),
    classification_level VARCHAR(50),
    validator_id INTEGER REFERENCES users(id),
    validation_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    confidence_score DECIMAL(3,2) NOT NULL DEFAULT 1.00,
    context_metadata JSONB,
    usage_count INTEGER DEFAULT 0,
    last_used TIMESTAMP WITH TIME ZONE,
    CONSTRAINT different_languages CHECK (source_language != target_language),
    CONSTRAINT valid_confidence CHECK (confidence_score >= 0 AND confidence_score <= 1)
);

CREATE INDEX idx_tm_source_target ON translation_memory(source_language, target_language);
CREATE INDEX idx_tm_source_text ON translation_memory USING gin(to_tsvector('english', source_text));
CREATE INDEX idx_tm_section_type ON translation_memory(section_type);
CREATE INDEX idx_tm_classification ON translation_memory(classification_level);
CREATE INDEX idx_tm_validation_date ON translation_memory(validation_date DESC);
```

**`terminology_database`**
```sql
CREATE TABLE terminology_database (
    id SERIAL PRIMARY KEY,
    term_english TEXT NOT NULL,
    term_french TEXT NOT NULL,
    category VARCHAR(100), -- 'job_classification', 'competency', 'accountability', etc.
    definition_english TEXT,
    definition_french TEXT,
    usage_context TEXT,
    validation_status VARCHAR(20) DEFAULT 'validated' CHECK (validation_status IN ('validated', 'pending', 'deprecated')),
    validated_by INTEGER REFERENCES users(id),
    validated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    usage_count INTEGER DEFAULT 0,
    alternate_translations JSONB,
    UNIQUE(term_english, term_french, category)
);

CREATE INDEX idx_terms_english ON terminology_database USING gin(to_tsvector('english', term_english));
CREATE INDEX idx_terms_french ON terminology_database USING gin(to_tsvector('french', term_french));
CREATE INDEX idx_terms_category ON terminology_database(category);
CREATE INDEX idx_terms_status ON terminology_database(validation_status);
```

**`bilingual_job_links`**
```sql
CREATE TABLE bilingual_job_links (
    id SERIAL PRIMARY KEY,
    english_job_id INTEGER REFERENCES job_descriptions(id) ON DELETE CASCADE,
    french_job_id INTEGER REFERENCES job_descriptions(id) ON DELETE CASCADE,
    concurrence_status VARCHAR(20) DEFAULT 'pending' CHECK (concurrence_status IN ('pending', 'validated', 'broken')),
    last_concurrence_check TIMESTAMP WITH TIME ZONE,
    concurrence_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT different_jobs CHECK (english_job_id != french_job_id),
    UNIQUE(english_job_id, french_job_id)
);

CREATE INDEX idx_bilingual_links_en ON bilingual_job_links(english_job_id);
CREATE INDEX idx_bilingual_links_fr ON bilingual_job_links(french_job_id);
CREATE INDEX idx_bilingual_concurrence ON bilingual_job_links(concurrence_status);
```

**`translation_sessions`**
```sql
CREATE TABLE translation_sessions (
    id SERIAL PRIMARY KEY,
    source_job_id INTEGER NOT NULL REFERENCES job_descriptions(id) ON DELETE CASCADE,
    target_job_id INTEGER REFERENCES job_descriptions(id) ON DELETE CASCADE,
    source_language VARCHAR(5) NOT NULL CHECK (source_language IN ('en', 'fr')),
    target_language VARCHAR(5) NOT NULL CHECK (target_language IN ('en', 'fr')),
    translator_id INTEGER NOT NULL REFERENCES users(id),
    session_start TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_end TIMESTAMP WITH TIME ZONE,
    total_sentences INTEGER DEFAULT 0,
    validated_count INTEGER DEFAULT 0,
    modified_count INTEGER DEFAULT 0,
    tm_exact_matches INTEGER DEFAULT 0,
    tm_fuzzy_matches INTEGER DEFAULT 0,
    mt_only_count INTEGER DEFAULT 0,
    configuration JSONB,
    CONSTRAINT different_languages CHECK (source_language != target_language)
);

CREATE INDEX idx_translation_sessions_source ON translation_sessions(source_job_id);
CREATE INDEX idx_translation_sessions_target ON translation_sessions(target_job_id);
CREATE INDEX idx_translation_sessions_translator ON translation_sessions(translator_id);
CREATE INDEX idx_translation_sessions_dates ON translation_sessions(session_start, session_end);
```

**`translation_suggestions`**
```sql
CREATE TABLE translation_suggestions (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES translation_sessions(id) ON DELETE CASCADE,
    source_section_id INTEGER NOT NULL REFERENCES job_sections(id) ON DELETE CASCADE,
    target_section_id INTEGER REFERENCES job_sections(id) ON DELETE CASCADE,
    sentence_index INTEGER NOT NULL,
    source_text TEXT NOT NULL,
    mt_suggestion TEXT, -- Machine translation suggestion
    tm_suggestion TEXT, -- Translation memory suggestion
    tm_match_score DECIMAL(3,2), -- TM similarity score (0.00-1.00)
    final_translation TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'modified', 'rejected')),
    translator_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    validated_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT valid_tm_score CHECK (tm_match_score IS NULL OR (tm_match_score >= 0 AND tm_match_score <= 1))
);

CREATE INDEX idx_translation_sugg_session ON translation_suggestions(session_id);
CREATE INDEX idx_translation_sugg_sections ON translation_suggestions(source_section_id, target_section_id);
CREATE INDEX idx_translation_sugg_status ON translation_suggestions(status);
```

**`concurrence_validations`**
```sql
CREATE TABLE concurrence_validations (
    id SERIAL PRIMARY KEY,
    bilingual_link_id INTEGER NOT NULL REFERENCES bilingual_job_links(id) ON DELETE CASCADE,
    validator_id INTEGER NOT NULL REFERENCES users(id),
    validation_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    validation_result VARCHAR(20) NOT NULL CHECK (validation_result IN ('pass', 'fail', 'conditional')),
    discrepancies JSONB, -- Store details of any discrepancies found
    notes TEXT,
    auto_validated BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_concurrence_val_link ON concurrence_validations(bilingual_link_id);
CREATE INDEX idx_concurrence_val_date ON concurrence_validations(validation_date DESC);
CREATE INDEX idx_concurrence_val_result ON concurrence_validations(validation_result);
```

#### Migration Script

**`backend/alembic/versions/YYYYMMDD_translation_tables.py`**
```python
"""Add translation memory and bilingual job support

Revision ID: YYYYMMDD_translation
Revises: YYYYMMDD_ai_improvement
Create Date: 2025-XX-XX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'YYYYMMDD_translation'
down_revision = 'YYYYMMDD_ai_improvement'


def upgrade():
    # Create translation_memory table
    op.execute("""
        CREATE TABLE translation_memory (
            id SERIAL PRIMARY KEY,
            source_language VARCHAR(5) NOT NULL CHECK (source_language IN ('en', 'fr')),
            target_language VARCHAR(5) NOT NULL CHECK (target_language IN ('en', 'fr')),
            source_text TEXT NOT NULL,
            target_text TEXT NOT NULL,
            section_type VARCHAR(100),
            classification_level VARCHAR(50),
            validator_id INTEGER REFERENCES users(id),
            validation_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            confidence_score DECIMAL(3,2) NOT NULL DEFAULT 1.00,
            context_metadata JSONB,
            usage_count INTEGER DEFAULT 0,
            last_used TIMESTAMP WITH TIME ZONE,
            CONSTRAINT different_languages CHECK (source_language != target_language),
            CONSTRAINT valid_confidence CHECK (confidence_score >= 0 AND confidence_score <= 1)
        );

        CREATE INDEX idx_tm_source_target ON translation_memory(source_language, target_language);
        CREATE INDEX idx_tm_source_text ON translation_memory USING gin(to_tsvector('english', source_text));
        CREATE INDEX idx_tm_section_type ON translation_memory(section_type);
        CREATE INDEX idx_tm_classification ON translation_memory(classification_level);
        CREATE INDEX idx_tm_validation_date ON translation_memory(validation_date DESC);
    """)

    # Create terminology_database table
    op.execute("""
        CREATE TABLE terminology_database (
            id SERIAL PRIMARY KEY,
            term_english TEXT NOT NULL,
            term_french TEXT NOT NULL,
            category VARCHAR(100),
            definition_english TEXT,
            definition_french TEXT,
            usage_context TEXT,
            validation_status VARCHAR(20) DEFAULT 'validated' CHECK (validation_status IN ('validated', 'pending', 'deprecated')),
            validated_by INTEGER REFERENCES users(id),
            validated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            usage_count INTEGER DEFAULT 0,
            alternate_translations JSONB,
            UNIQUE(term_english, term_french, category)
        );

        CREATE INDEX idx_terms_english ON terminology_database USING gin(to_tsvector('english', term_english));
        CREATE INDEX idx_terms_french ON terminology_database USING gin(to_tsvector('french', term_french));
        CREATE INDEX idx_terms_category ON terminology_database(category);
        CREATE INDEX idx_terms_status ON terminology_database(validation_status);
    """)

    # Create bilingual_job_links table
    op.execute("""
        CREATE TABLE bilingual_job_links (
            id SERIAL PRIMARY KEY,
            english_job_id INTEGER REFERENCES job_descriptions(id) ON DELETE CASCADE,
            french_job_id INTEGER REFERENCES job_descriptions(id) ON DELETE CASCADE,
            concurrence_status VARCHAR(20) DEFAULT 'pending' CHECK (concurrence_status IN ('pending', 'validated', 'broken')),
            last_concurrence_check TIMESTAMP WITH TIME ZONE,
            concurrence_metadata JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            CONSTRAINT different_jobs CHECK (english_job_id != french_job_id),
            UNIQUE(english_job_id, french_job_id)
        );

        CREATE INDEX idx_bilingual_links_en ON bilingual_job_links(english_job_id);
        CREATE INDEX idx_bilingual_links_fr ON bilingual_job_links(french_job_id);
        CREATE INDEX idx_bilingual_concurrence ON bilingual_job_links(concurrence_status);
    """)

    # Create translation_sessions table
    op.execute("""
        CREATE TABLE translation_sessions (
            id SERIAL PRIMARY KEY,
            source_job_id INTEGER NOT NULL REFERENCES job_descriptions(id) ON DELETE CASCADE,
            target_job_id INTEGER REFERENCES job_descriptions(id) ON DELETE CASCADE,
            source_language VARCHAR(5) NOT NULL CHECK (source_language IN ('en', 'fr')),
            target_language VARCHAR(5) NOT NULL CHECK (target_language IN ('en', 'fr')),
            translator_id INTEGER NOT NULL REFERENCES users(id),
            session_start TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            session_end TIMESTAMP WITH TIME ZONE,
            total_sentences INTEGER DEFAULT 0,
            validated_count INTEGER DEFAULT 0,
            modified_count INTEGER DEFAULT 0,
            tm_exact_matches INTEGER DEFAULT 0,
            tm_fuzzy_matches INTEGER DEFAULT 0,
            mt_only_count INTEGER DEFAULT 0,
            configuration JSONB,
            CONSTRAINT different_languages CHECK (source_language != target_language)
        );

        CREATE INDEX idx_translation_sessions_source ON translation_sessions(source_job_id);
        CREATE INDEX idx_translation_sessions_target ON translation_sessions(target_job_id);
        CREATE INDEX idx_translation_sessions_translator ON translation_sessions(translator_id);
        CREATE INDEX idx_translation_sessions_dates ON translation_sessions(session_start, session_end);
    """)

    # Create translation_suggestions table
    op.execute("""
        CREATE TABLE translation_suggestions (
            id SERIAL PRIMARY KEY,
            session_id INTEGER NOT NULL REFERENCES translation_sessions(id) ON DELETE CASCADE,
            source_section_id INTEGER NOT NULL REFERENCES job_sections(id) ON DELETE CASCADE,
            target_section_id INTEGER REFERENCES job_sections(id) ON DELETE CASCADE,
            sentence_index INTEGER NOT NULL,
            source_text TEXT NOT NULL,
            mt_suggestion TEXT,
            tm_suggestion TEXT,
            tm_match_score DECIMAL(3,2),
            final_translation TEXT,
            status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'modified', 'rejected')),
            translator_notes TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            validated_at TIMESTAMP WITH TIME ZONE,
            CONSTRAINT valid_tm_score CHECK (tm_match_score IS NULL OR (tm_match_score >= 0 AND tm_match_score <= 1))
        );

        CREATE INDEX idx_translation_sugg_session ON translation_suggestions(session_id);
        CREATE INDEX idx_translation_sugg_sections ON translation_suggestions(source_section_id, target_section_id);
        CREATE INDEX idx_translation_sugg_status ON translation_suggestions(status);
    """)

    # Create concurrence_validations table
    op.execute("""
        CREATE TABLE concurrence_validations (
            id SERIAL PRIMARY KEY,
            bilingual_link_id INTEGER NOT NULL REFERENCES bilingual_job_links(id) ON DELETE CASCADE,
            validator_id INTEGER NOT NULL REFERENCES users(id),
            validation_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            validation_result VARCHAR(20) NOT NULL CHECK (validation_result IN ('pass', 'fail', 'conditional')),
            discrepancies JSONB,
            notes TEXT,
            auto_validated BOOLEAN DEFAULT FALSE
        );

        CREATE INDEX idx_concurrence_val_link ON concurrence_validations(bilingual_link_id);
        CREATE INDEX idx_concurrence_val_date ON concurrence_validations(validation_date DESC);
        CREATE INDEX idx_concurrence_val_result ON concurrence_validations(validation_result);
    """)


def downgrade():
    op.execute("DROP TABLE IF EXISTS concurrence_validations CASCADE;")
    op.execute("DROP TABLE IF EXISTS translation_suggestions CASCADE;")
    op.execute("DROP TABLE IF EXISTS translation_sessions CASCADE;")
    op.execute("DROP TABLE IF EXISTS bilingual_job_links CASCADE;")
    op.execute("DROP TABLE IF EXISTS terminology_database CASCADE;")
    op.execute("DROP TABLE IF EXISTS translation_memory CASCADE;")
```

### 1.2 Backend Models

**`backend/src/jd_ingestion/database/models.py`** (additions)
```python
from sqlalchemy import Column, Integer, String, Text, DECIMAL, TIMESTAMP, ForeignKey, CheckConstraint, Index, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime


class TranslationMemory(Base):
    __tablename__ = 'translation_memory'

    id = Column(Integer, primary_key=True)
    source_language = Column(String(5), nullable=False)
    target_language = Column(String(5), nullable=False)
    source_text = Column(Text, nullable=False)
    target_text = Column(Text, nullable=False)
    section_type = Column(String(100), nullable=True)
    classification_level = Column(String(50), nullable=True)
    validator_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    validation_date = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    confidence_score = Column(DECIMAL(3, 2), nullable=False, default=1.00)
    context_metadata = Column(JSONB, nullable=True)
    usage_count = Column(Integer, default=0)
    last_used = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    validator = relationship("User", foreign_keys=[validator_id])

    __table_args__ = (
        CheckConstraint("source_language != target_language", name="different_languages"),
        CheckConstraint("source_language IN ('en', 'fr')", name="valid_source_lang"),
        CheckConstraint("target_language IN ('en', 'fr')", name="valid_target_lang"),
        CheckConstraint("confidence_score >= 0 AND confidence_score <= 1", name="valid_confidence"),
        Index('idx_tm_source_target', 'source_language', 'target_language'),
        Index('idx_tm_section_type', 'section_type'),
        Index('idx_tm_classification', 'classification_level'),
        Index('idx_tm_validation_date', 'validation_date'),
    )


class TerminologyDatabase(Base):
    __tablename__ = 'terminology_database'

    id = Column(Integer, primary_key=True)
    term_english = Column(Text, nullable=False)
    term_french = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)
    definition_english = Column(Text, nullable=True)
    definition_french = Column(Text, nullable=True)
    usage_context = Column(Text, nullable=True)
    validation_status = Column(String(20), nullable=False, default='validated')
    validated_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    validated_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    usage_count = Column(Integer, default=0)
    alternate_translations = Column(JSONB, nullable=True)

    # Relationships
    validator = relationship("User", foreign_keys=[validated_by])

    __table_args__ = (
        UniqueConstraint('term_english', 'term_french', 'category', name='unique_term_pair'),
        CheckConstraint("validation_status IN ('validated', 'pending', 'deprecated')", name="valid_status"),
        Index('idx_terms_category', 'category'),
        Index('idx_terms_status', 'validation_status'),
    )


class BilingualJobLink(Base):
    __tablename__ = 'bilingual_job_links'

    id = Column(Integer, primary_key=True)
    english_job_id = Column(Integer, ForeignKey('job_descriptions.id', ondelete='CASCADE'), nullable=True)
    french_job_id = Column(Integer, ForeignKey('job_descriptions.id', ondelete='CASCADE'), nullable=True)
    concurrence_status = Column(String(20), nullable=False, default='pending')
    last_concurrence_check = Column(TIMESTAMP(timezone=True), nullable=True)
    concurrence_metadata = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    english_job = relationship("JobDescription", foreign_keys=[english_job_id], back_populates="bilingual_en_link")
    french_job = relationship("JobDescription", foreign_keys=[french_job_id], back_populates="bilingual_fr_link")
    validations = relationship("ConcurrenceValidation", back_populates="bilingual_link", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("english_job_id != french_job_id", name="different_jobs"),
        CheckConstraint("concurrence_status IN ('pending', 'validated', 'broken')", name="valid_concurrence"),
        UniqueConstraint('english_job_id', 'french_job_id', name='unique_bilingual_pair'),
        Index('idx_bilingual_links_en', 'english_job_id'),
        Index('idx_bilingual_links_fr', 'french_job_id'),
        Index('idx_bilingual_concurrence', 'concurrence_status'),
    )


class TranslationSession(Base):
    __tablename__ = 'translation_sessions'

    id = Column(Integer, primary_key=True)
    source_job_id = Column(Integer, ForeignKey('job_descriptions.id', ondelete='CASCADE'), nullable=False)
    target_job_id = Column(Integer, ForeignKey('job_descriptions.id', ondelete='CASCADE'), nullable=True)
    source_language = Column(String(5), nullable=False)
    target_language = Column(String(5), nullable=False)
    translator_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    session_start = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    session_end = Column(TIMESTAMP(timezone=True), nullable=True)
    total_sentences = Column(Integer, default=0)
    validated_count = Column(Integer, default=0)
    modified_count = Column(Integer, default=0)
    tm_exact_matches = Column(Integer, default=0)
    tm_fuzzy_matches = Column(Integer, default=0)
    mt_only_count = Column(Integer, default=0)
    configuration = Column(JSONB, nullable=True)

    # Relationships
    source_job = relationship("JobDescription", foreign_keys=[source_job_id])
    target_job = relationship("JobDescription", foreign_keys=[target_job_id])
    translator = relationship("User", foreign_keys=[translator_id])
    suggestions = relationship("TranslationSuggestion", back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("source_language != target_language", name="different_languages"),
        CheckConstraint("source_language IN ('en', 'fr')", name="valid_source_lang"),
        CheckConstraint("target_language IN ('en', 'fr')", name="valid_target_lang"),
        Index('idx_translation_sessions_source', 'source_job_id'),
        Index('idx_translation_sessions_target', 'target_job_id'),
        Index('idx_translation_sessions_translator', 'translator_id'),
        Index('idx_translation_sessions_dates', 'session_start', 'session_end'),
    )


class TranslationSuggestion(Base):
    __tablename__ = 'translation_suggestions'

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('translation_sessions.id', ondelete='CASCADE'), nullable=False)
    source_section_id = Column(Integer, ForeignKey('job_sections.id', ondelete='CASCADE'), nullable=False)
    target_section_id = Column(Integer, ForeignKey('job_sections.id', ondelete='CASCADE'), nullable=True)
    sentence_index = Column(Integer, nullable=False)
    source_text = Column(Text, nullable=False)
    mt_suggestion = Column(Text, nullable=True)
    tm_suggestion = Column(Text, nullable=True)
    tm_match_score = Column(DECIMAL(3, 2), nullable=True)
    final_translation = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default='pending')
    translator_notes = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    validated_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    session = relationship("TranslationSession", back_populates="suggestions")
    source_section = relationship("JobSection", foreign_keys=[source_section_id])
    target_section = relationship("JobSection", foreign_keys=[target_section_id])

    __table_args__ = (
        CheckConstraint("status IN ('pending', 'accepted', 'modified', 'rejected')", name="valid_status"),
        CheckConstraint("tm_match_score IS NULL OR (tm_match_score >= 0 AND tm_match_score <= 1)", name="valid_tm_score"),
        Index('idx_translation_sugg_session', 'session_id'),
        Index('idx_translation_sugg_sections', 'source_section_id', 'target_section_id'),
        Index('idx_translation_sugg_status', 'status'),
    )


class ConcurrenceValidation(Base):
    __tablename__ = 'concurrence_validations'

    id = Column(Integer, primary_key=True)
    bilingual_link_id = Column(Integer, ForeignKey('bilingual_job_links.id', ondelete='CASCADE'), nullable=False)
    validator_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    validation_date = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    validation_result = Column(String(20), nullable=False)
    discrepancies = Column(JSONB, nullable=True)
    notes = Column(Text, nullable=True)
    auto_validated = Column(Boolean, default=False)

    # Relationships
    bilingual_link = relationship("BilingualJobLink", back_populates="validations")
    validator = relationship("User", foreign_keys=[validator_id])

    __table_args__ = (
        CheckConstraint("validation_result IN ('pass', 'fail', 'conditional')", name="valid_result"),
        Index('idx_concurrence_val_link', 'bilingual_link_id'),
        Index('idx_concurrence_val_date', 'validation_date'),
        Index('idx_concurrence_val_result', 'validation_result'),
    )


# Update JobDescription model to include bilingual relationships
JobDescription.bilingual_en_link = relationship(
    "BilingualJobLink",
    foreign_keys="BilingualJobLink.english_job_id",
    back_populates="english_job",
    uselist=False
)
JobDescription.bilingual_fr_link = relationship(
    "BilingualJobLink",
    foreign_keys="BilingualJobLink.french_job_id",
    back_populates="french_job",
    uselist=False
)
```

---

*Due to length constraints, I'll create a summary document of what's been implemented and what remains. Let me complete the Translation Mode roadmap and then create a comprehensive implementation status report.*
