# AI Improvement Mode - Implementation Roadmap

## Overview

Comprehensive implementation plan for sentence-level AI-assisted job description improvement with accept/reject/modify controls and learning feedback loops.

**Implementation Date**: TBD (after job descriptions are properly ingested)
**Estimated Effort**: 4-6 weeks
**Priority**: High (Phase 7)

---

## Phase 1: Backend Infrastructure (Week 1)

### 1.1 Database Schema Extensions

#### New Tables

**`ai_suggestions`**
```sql
CREATE TABLE ai_suggestions (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES job_descriptions(id) ON DELETE CASCADE,
    section_id INTEGER NOT NULL REFERENCES job_sections(id) ON DELETE CASCADE,
    suggestion_type VARCHAR(50) NOT NULL, -- 'clarity', 'completeness', 'consistency', 'professionalism', 'specificity'
    original_text TEXT NOT NULL,
    suggested_text TEXT NOT NULL,
    rationale TEXT NOT NULL,
    confidence_score DECIMAL(3,2) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    sentence_index INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- 'pending', 'accepted', 'rejected', 'modified'
    modified_text TEXT,
    advisor_feedback TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    reviewed_by INTEGER REFERENCES users(id),
    CONSTRAINT valid_status CHECK (status IN ('pending', 'accepted', 'rejected', 'modified'))
);

CREATE INDEX idx_ai_suggestions_job_section ON ai_suggestions(job_id, section_id);
CREATE INDEX idx_ai_suggestions_status ON ai_suggestions(status);
CREATE INDEX idx_ai_suggestions_reviewed_at ON ai_suggestions(reviewed_at);
```

**`ai_improvement_sessions`**
```sql
CREATE TABLE ai_improvement_sessions (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES job_descriptions(id) ON DELETE CASCADE,
    advisor_id INTEGER NOT NULL REFERENCES users(id),
    session_start TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_end TIMESTAMP WITH TIME ZONE,
    total_suggestions INTEGER DEFAULT 0,
    accepted_count INTEGER DEFAULT 0,
    rejected_count INTEGER DEFAULT 0,
    modified_count INTEGER DEFAULT 0,
    configuration JSONB, -- stores granularity, aggressiveness, focus areas
    quality_score_before DECIMAL(3,2),
    quality_score_after DECIMAL(3,2),
    iteration_number INTEGER DEFAULT 1,
    CONSTRAINT valid_quality_scores CHECK (
        quality_score_before IS NULL OR (quality_score_before >= 0 AND quality_score_before <= 1)
    ) AND (
        quality_score_after IS NULL OR (quality_score_after >= 0 AND quality_score_after <= 1)
    )
);

CREATE INDEX idx_ai_sessions_job ON ai_improvement_sessions(job_id);
CREATE INDEX idx_ai_sessions_advisor ON ai_improvement_sessions(advisor_id);
CREATE INDEX idx_ai_sessions_dates ON ai_improvement_sessions(session_start, session_end);
```

**`ai_learning_feedback`**
```sql
CREATE TABLE ai_learning_feedback (
    id SERIAL PRIMARY KEY,
    suggestion_id INTEGER NOT NULL REFERENCES ai_suggestions(id) ON DELETE CASCADE,
    section_type VARCHAR(100) NOT NULL,
    classification_level VARCHAR(50),
    pattern_type VARCHAR(50), -- 'high_acceptance', 'low_acceptance', 'modification_pattern'
    feedback_data JSONB NOT NULL, -- stores detailed pattern analysis
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_ai_feedback_suggestion ON ai_learning_feedback(suggestion_id);
CREATE INDEX idx_ai_feedback_pattern ON ai_learning_feedback(pattern_type);
```

#### Migration Script
```python
# backend/alembic/versions/YYYYMMDD_ai_improvement_tables.py

def upgrade():
    # Create tables
    op.execute("""
        CREATE TABLE ai_suggestions (
            -- schema from above
        );

        CREATE TABLE ai_improvement_sessions (
            -- schema from above
        );

        CREATE TABLE ai_learning_feedback (
            -- schema from above
        );
    """)

    # Create indexes
    op.execute("""
        CREATE INDEX idx_ai_suggestions_job_section ON ai_suggestions(job_id, section_id);
        -- additional indexes
    """)

def downgrade():
    op.execute("DROP TABLE IF EXISTS ai_learning_feedback CASCADE;")
    op.execute("DROP TABLE IF EXISTS ai_improvement_sessions CASCADE;")
    op.execute("DROP TABLE IF EXISTS ai_suggestions CASCADE;")
```

### 1.2 Backend Models

**`backend/src/jd_ingestion/database/models.py`**
```python
from sqlalchemy import Column, Integer, String, Text, DECIMAL, TIMESTAMP, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime

class AISuggestion(Base):
    __tablename__ = 'ai_suggestions'

    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey('job_descriptions.id', ondelete='CASCADE'), nullable=False)
    section_id = Column(Integer, ForeignKey('job_sections.id', ondelete='CASCADE'), nullable=False)
    suggestion_type = Column(String(50), nullable=False)
    original_text = Column(Text, nullable=False)
    suggested_text = Column(Text, nullable=False)
    rationale = Column(Text, nullable=False)
    confidence_score = Column(DECIMAL(3, 2), nullable=False)
    sentence_index = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default='pending')
    modified_text = Column(Text, nullable=True)
    advisor_feedback = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    reviewed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    reviewed_by = Column(Integer, ForeignKey('users.id'), nullable=True)

    # Relationships
    job = relationship("JobDescription", back_populates="ai_suggestions")
    section = relationship("JobSection", back_populates="ai_suggestions")
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    learning_feedback = relationship("AILearningFeedback", back_populates="suggestion", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("confidence_score >= 0 AND confidence_score <= 1", name="valid_confidence"),
        CheckConstraint("status IN ('pending', 'accepted', 'rejected', 'modified')", name="valid_status"),
        Index('idx_ai_suggestions_job_section', 'job_id', 'section_id'),
        Index('idx_ai_suggestions_status', 'status'),
        Index('idx_ai_suggestions_reviewed_at', 'reviewed_at'),
    )


class AIImprovementSession(Base):
    __tablename__ = 'ai_improvement_sessions'

    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey('job_descriptions.id', ondelete='CASCADE'), nullable=False)
    advisor_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    session_start = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    session_end = Column(TIMESTAMP(timezone=True), nullable=True)
    total_suggestions = Column(Integer, default=0)
    accepted_count = Column(Integer, default=0)
    rejected_count = Column(Integer, default=0)
    modified_count = Column(Integer, default=0)
    configuration = Column(JSONB, nullable=True)
    quality_score_before = Column(DECIMAL(3, 2), nullable=True)
    quality_score_after = Column(DECIMAL(3, 2), nullable=True)
    iteration_number = Column(Integer, default=1)

    # Relationships
    job = relationship("JobDescription", back_populates="improvement_sessions")
    advisor = relationship("User", foreign_keys=[advisor_id])

    __table_args__ = (
        Index('idx_ai_sessions_job', 'job_id'),
        Index('idx_ai_sessions_advisor', 'advisor_id'),
        Index('idx_ai_sessions_dates', 'session_start', 'session_end'),
    )


class AILearningFeedback(Base):
    __tablename__ = 'ai_learning_feedback'

    id = Column(Integer, primary_key=True)
    suggestion_id = Column(Integer, ForeignKey('ai_suggestions.id', ondelete='CASCADE'), nullable=False)
    section_type = Column(String(100), nullable=False)
    classification_level = Column(String(50), nullable=True)
    pattern_type = Column(String(50), nullable=False)
    feedback_data = Column(JSONB, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)

    # Relationships
    suggestion = relationship("AISuggestion", back_populates="learning_feedback")

    __table_args__ = (
        Index('idx_ai_feedback_suggestion', 'suggestion_id'),
        Index('idx_ai_feedback_pattern', 'pattern_type'),
    )


# Update existing models with new relationships
JobDescription.ai_suggestions = relationship("AISuggestion", back_populates="job", cascade="all, delete-orphan")
JobDescription.improvement_sessions = relationship("AIImprovementSession", back_populates="job", cascade="all, delete-orphan")

JobSection.ai_suggestions = relationship("AISuggestion", back_populates="section", cascade="all, delete-orphan")
```

### 1.3 OpenAI Service Integration

**`backend/src/jd_ingestion/services/ai_improvement_service.py`**
```python
"""
AI Improvement Service
Handles OpenAI API integration for job description improvement suggestions
"""

import openai
from typing import List, Dict, Optional
from dataclasses import dataclass
import re
from jd_ingestion.config.settings import settings

openai.api_key = settings.OPENAI_API_KEY


@dataclass
class ImprovementSuggestion:
    """Data class for a single improvement suggestion"""
    sentence_index: int
    original_text: str
    suggested_text: str
    rationale: str
    suggestion_type: str
    confidence_score: float


class AIImprovementService:
    """Service for generating AI-powered job description improvements"""

    def __init__(self):
        self.model = "gpt-4-turbo-preview"  # or "gpt-4o" when available
        self.max_tokens = 2000
        self.temperature = 0.3  # Lower for more consistent suggestions

    async def analyze_section(
        self,
        section_content: str,
        section_type: str,
        classification_level: Optional[str] = None,
        focus_areas: Optional[List[str]] = None,
        granularity: str = "sentence",
        aggressiveness: str = "moderate"
    ) -> List[ImprovementSuggestion]:
        """
        Analyze a job description section and generate improvement suggestions

        Args:
            section_content: The text content of the section
            section_type: Type of section (e.g., 'general_accountability')
            classification_level: Job classification (e.g., 'EX-01')
            focus_areas: List of improvement focus areas
            granularity: 'sentence', 'clause', or 'paragraph'
            aggressiveness: 'conservative', 'moderate', or 'aggressive'

        Returns:
            List of ImprovementSuggestion objects
        """

        # Split content into sentences
        sentences = self._split_into_sentences(section_content)

        # Build system prompt
        system_prompt = self._build_system_prompt(
            section_type=section_type,
            classification_level=classification_level,
            focus_areas=focus_areas or ["clarity", "professionalism"],
            aggressiveness=aggressiveness
        )

        # Build user prompt
        user_prompt = self._build_user_prompt(sentences)

        # Call OpenAI API
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            # Parse response into suggestions
            suggestions = self._parse_ai_response(
                response.choices[0].message.content,
                sentences
            )

            return suggestions

        except openai.error.RateLimitError:
            raise Exception("OpenAI API rate limit exceeded. Please try again later.")
        except openai.error.APIError as e:
            raise Exception(f"OpenAI API error: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to generate AI suggestions: {str(e)}")

    def _split_into_sentences(self, content: str) -> List[str]:
        """Split content into sentences using regex"""
        # Simple sentence splitting (can be improved)
        sentences = re.split(r'(?<=[.!?])\s+', content)
        return [s.strip() for s in sentences if s.strip()]

    def _build_system_prompt(
        self,
        section_type: str,
        classification_level: Optional[str],
        focus_areas: List[str],
        aggressiveness: str
    ) -> str:
        """Build system prompt for OpenAI"""

        focus_descriptions = {
            "clarity": "Remove ambiguous language, simplify complex sentences, improve readability",
            "completeness": "Identify missing information, suggest additional context",
            "consistency": "Align with organizational terminology, standardize formatting",
            "professionalism": "Elevate language to executive level, apply government communication standards",
            "specificity": "Replace vague terms with specific details, quantify where appropriate"
        }

        focus_text = "\n".join([f"- {area.capitalize()}: {focus_descriptions.get(area, '')}"
                                for area in focus_areas])

        aggressiveness_instructions = {
            "conservative": "Only suggest clear, obvious improvements. Preserve original phrasing when acceptable.",
            "moderate": "Balance improvement with preserving the author's voice. Suggest meaningful enhancements.",
            "aggressive": "Extensively restructure and rewrite for maximum clarity and professionalism."
        }

        return f"""You are an expert job description editor specializing in Canadian government job descriptions at the {classification_level or 'executive'} level.

Your task is to analyze the '{section_type}' section and suggest improvements focusing on:
{focus_text}

Improvement approach: {aggressiveness_instructions[aggressiveness]}

For each sentence that could be improved, provide:
1. The sentence index (0-based)
2. The original text
3. Your suggested improvement
4. A brief rationale (1-2 sentences)
5. The type of improvement (one of: {', '.join(focus_areas)})
6. A confidence score (0.0-1.0) indicating how certain you are this is an improvement

Format your response as JSON:
{{
  "suggestions": [
    {{
      "sentence_index": 0,
      "original_text": "...",
      "suggested_text": "...",
      "rationale": "...",
      "suggestion_type": "clarity",
      "confidence_score": 0.85
    }}
  ]
}}

Only suggest improvements for sentences that genuinely need them. If a sentence is already high-quality, skip it.
"""

    def _build_user_prompt(self, sentences: List[str]) -> str:
        """Build user prompt with numbered sentences"""
        numbered_sentences = "\n".join([f"{i}. {s}" for i, s in enumerate(sentences)])
        return f"""Analyze the following sentences and suggest improvements:\n\n{numbered_sentences}"""

    def _parse_ai_response(
        self,
        response_text: str,
        original_sentences: List[str]
    ) -> List[ImprovementSuggestion]:
        """Parse OpenAI response into ImprovementSuggestion objects"""
        import json

        try:
            response_data = json.loads(response_text)
            suggestions = []

            for item in response_data.get("suggestions", []):
                suggestion = ImprovementSuggestion(
                    sentence_index=item["sentence_index"],
                    original_text=item["original_text"],
                    suggested_text=item["suggested_text"],
                    rationale=item["rationale"],
                    suggestion_type=item["suggestion_type"],
                    confidence_score=float(item["confidence_score"])
                )
                suggestions.append(suggestion)

            return suggestions

        except json.JSONDecodeError:
            # Fallback: try to extract suggestions from text
            return []
        except Exception as e:
            raise Exception(f"Failed to parse AI response: {str(e)}")

    def calculate_quality_score(self, section_content: str) -> float:
        """
        Calculate a quality score for section content
        Uses heuristics like readability, completeness, etc.
        Returns score between 0.0 and 1.0
        """
        # Implement quality scoring logic
        # For now, return a placeholder
        # TODO: Implement Flesch-Kincaid readability score
        # TODO: Check for placeholder text
        # TODO: Analyze sentence structure
        return 0.75  # Placeholder
```

### 1.4 API Endpoints

**`backend/src/jd_ingestion/api/endpoints/ai_improvement.py`**
```python
"""
AI Improvement API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from jd_ingestion.database.connection import get_async_session
from jd_ingestion.database.models import (
    JobDescription, JobSection, AISuggestion,
    AIImprovementSession, AILearningFeedback
)
from jd_ingestion.services.ai_improvement_service import AIImprovementService
from jd_ingestion.api.dependencies import get_api_key
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai-improvement", tags=["AI Improvement"])


# Request/Response Models
class ImprovementConfiguration(BaseModel):
    """Configuration for AI improvement session"""
    granularity: str = Field(default="sentence", pattern="^(sentence|clause|paragraph)$")
    aggressiveness: str = Field(default="moderate", pattern="^(conservative|moderate|aggressive)$")
    focus_areas: List[str] = Field(default=["clarity", "professionalism"])
    auto_accept_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class SuggestionResponse(BaseModel):
    """Response model for a single suggestion"""
    id: int
    sentence_index: int
    original_text: str
    suggested_text: str
    rationale: str
    suggestion_type: str
    confidence_score: float
    status: str


class SessionStartRequest(BaseModel):
    """Request to start AI improvement session"""
    job_id: int
    configuration: ImprovementConfiguration


class SessionStartResponse(BaseModel):
    """Response after starting session"""
    session_id: int
    job_id: int
    sections_to_improve: List[int]
    quality_score_before: float


class SectionAnalysisRequest(BaseModel):
    """Request to analyze a specific section"""
    session_id: int
    section_id: int


class SectionAnalysisResponse(BaseModel):
    """Response with AI suggestions for section"""
    section_id: int
    section_type: str
    suggestions: List[SuggestionResponse]
    total_suggestions: int


class SuggestionActionRequest(BaseModel):
    """Request to accept/reject/modify suggestion"""
    suggestion_id: int
    action: str = Field(pattern="^(accept|reject|modify)$")
    modified_text: Optional[str] = None
    advisor_feedback: Optional[str] = None


class SessionCompleteRequest(BaseModel):
    """Request to complete improvement session"""
    session_id: int


class SessionCompleteResponse(BaseModel):
    """Response after completing session"""
    session_id: int
    total_suggestions: int
    accepted_count: int
    rejected_count: int
    modified_count: int
    quality_score_after: float
    improvement_percentage: float


# Endpoints

@router.post("/sessions/start", response_model=SessionStartResponse)
async def start_improvement_session(
    request: SessionStartRequest,
    db: AsyncSession = Depends(get_async_session),
    api_key: str = Security(get_api_key)
):
    """
    Start a new AI improvement session for a job description
    """
    try:
        # Verify job exists
        job_query = select(JobDescription).where(JobDescription.id == request.job_id)
        job_result = await db.execute(job_query)
        job = job_result.scalar_one_or_none()

        if not job:
            raise HTTPException(status_code=404, detail="Job description not found")

        # Get all sections for job
        sections_query = select(JobSection).where(JobSection.job_id == request.job_id)
        sections_result = await db.execute(sections_query)
        sections = sections_result.scalars().all()

        if not sections:
            raise HTTPException(status_code=400, detail="Job has no sections to improve")

        # Calculate quality score before improvement
        ai_service = AIImprovementService()
        quality_before = ai_service.calculate_quality_score(job.raw_content or "")

        # Determine iteration number
        existing_sessions_query = select(AIImprovementSession).where(
            AIImprovementSession.job_id == request.job_id
        )
        existing_result = await db.execute(existing_sessions_query)
        existing_sessions = existing_result.scalars().all()
        iteration = len(existing_sessions) + 1

        # Create improvement session
        session = AIImprovementSession(
            job_id=request.job_id,
            advisor_id=1,  # TODO: Get from authenticated user
            configuration=request.configuration.dict(),
            quality_score_before=quality_before,
            iteration_number=iteration
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

        logger.info(f"Started AI improvement session {session.id} for job {request.job_id}")

        return SessionStartResponse(
            session_id=session.id,
            job_id=request.job_id,
            sections_to_improve=[s.id for s in sections],
            quality_score_before=quality_before
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting improvement session: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to start improvement session")


@router.post("/sections/analyze", response_model=SectionAnalysisResponse)
async def analyze_section(
    request: SectionAnalysisRequest,
    db: AsyncSession = Depends(get_async_session),
    api_key: str = Security(get_api_key)
):
    """
    Analyze a specific section and generate AI improvement suggestions
    """
    try:
        # Verify session exists
        session_query = select(AIImprovementSession).where(
            AIImprovementSession.id == request.session_id
        )
        session_result = await db.execute(session_query)
        session = session_result.scalar_one_or_none()

        if not session:
            raise HTTPException(status_code=404, detail="Improvement session not found")

        # Verify section exists and belongs to job
        section_query = select(JobSection).where(
            JobSection.id == request.section_id,
            JobSection.job_id == session.job_id
        )
        section_result = await db.execute(section_query)
        section = section_result.scalar_one_or_none()

        if not section:
            raise HTTPException(status_code=404, detail="Section not found")

        # Get job for classification info
        job_query = select(JobDescription).where(JobDescription.id == session.job_id)
        job_result = await db.execute(job_query)
        job = job_result.scalar_one_or_none()

        # Generate AI suggestions
        ai_service = AIImprovementService()
        config = session.configuration or {}

        suggestions = await ai_service.analyze_section(
            section_content=section.section_content,
            section_type=section.section_type,
            classification_level=job.classification if job else None,
            focus_areas=config.get("focus_areas"),
            granularity=config.get("granularity", "sentence"),
            aggressiveness=config.get("aggressiveness", "moderate")
        )

        # Save suggestions to database
        db_suggestions = []
        for sugg in suggestions:
            db_sugg = AISuggestion(
                job_id=session.job_id,
                section_id=request.section_id,
                suggestion_type=sugg.suggestion_type,
                original_text=sugg.original_text,
                suggested_text=sugg.suggested_text,
                rationale=sugg.rationale,
                confidence_score=sugg.confidence_score,
                sentence_index=sugg.sentence_index,
                status='pending'
            )
            db.add(db_sugg)
            db_suggestions.append(db_sugg)

        # Update session total suggestions
        session.total_suggestions += len(suggestions)

        await db.commit()

        # Refresh to get IDs
        for db_sugg in db_suggestions:
            await db.refresh(db_sugg)

        logger.info(f"Generated {len(suggestions)} suggestions for section {request.section_id}")

        return SectionAnalysisResponse(
            section_id=request.section_id,
            section_type=section.section_type,
            suggestions=[
                SuggestionResponse(
                    id=s.id,
                    sentence_index=s.sentence_index,
                    original_text=s.original_text,
                    suggested_text=s.suggested_text,
                    rationale=s.rationale,
                    suggestion_type=s.suggestion_type,
                    confidence_score=float(s.confidence_score),
                    status=s.status
                )
                for s in db_suggestions
            ],
            total_suggestions=len(suggestions)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing section: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to analyze section")


@router.post("/suggestions/action")
async def handle_suggestion_action(
    request: SuggestionActionRequest,
    db: AsyncSession = Depends(get_async_session),
    api_key: str = Security(get_api_key)
):
    """
    Handle accept/reject/modify action on a suggestion
    """
    try:
        # Get suggestion
        suggestion_query = select(AISuggestion).where(
            AISuggestion.id == request.suggestion_id
        )
        suggestion_result = await db.execute(suggestion_query)
        suggestion = suggestion_result.scalar_one_or_none()

        if not suggestion:
            raise HTTPException(status_code=404, detail="Suggestion not found")

        # Update suggestion based on action
        if request.action == "accept":
            suggestion.status = "accepted"
            # Update session accepted count
            session_query = select(AIImprovementSession).where(
                AIImprovementSession.job_id == suggestion.job_id
            ).order_by(AIImprovementSession.session_start.desc())
            session_result = await db.execute(session_query)
            session = session_result.scalar_one_or_none()
            if session:
                session.accepted_count += 1

        elif request.action == "reject":
            suggestion.status = "rejected"
            suggestion.advisor_feedback = request.advisor_feedback
            # Update session rejected count
            session_query = select(AIImprovementSession).where(
                AIImprovementSession.job_id == suggestion.job_id
            ).order_by(AIImprovementSession.session_start.desc())
            session_result = await db.execute(session_query)
            session = session_result.scalar_one_or_none()
            if session:
                session.rejected_count += 1

            # Store learning feedback
            feedback = AILearningFeedback(
                suggestion_id=suggestion.id,
                section_type=suggestion.section.section_type,
                classification_level=suggestion.job.classification,
                pattern_type="rejection",
                feedback_data={
                    "reason": request.advisor_feedback,
                    "suggestion_type": suggestion.suggestion_type
                }
            )
            db.add(feedback)

        elif request.action == "modify":
            if not request.modified_text:
                raise HTTPException(status_code=400, detail="modified_text required for modify action")
            suggestion.status = "modified"
            suggestion.modified_text = request.modified_text
            suggestion.advisor_feedback = request.advisor_feedback
            # Update session modified count
            session_query = select(AIImprovementSession).where(
                AIImprovementSession.job_id == suggestion.job_id
            ).order_by(AIImprovementSession.session_start.desc())
            session_result = await db.execute(session_query)
            session = session_result.scalar_one_or_none()
            if session:
                session.modified_count += 1

            # Store learning feedback for modifications
            feedback = AILearningFeedback(
                suggestion_id=suggestion.id,
                section_type=suggestion.section.section_type,
                classification_level=suggestion.job.classification,
                pattern_type="modification",
                feedback_data={
                    "original_suggestion": suggestion.suggested_text,
                    "modified_version": request.modified_text,
                    "advisor_notes": request.advisor_feedback
                }
            )
            db.add(feedback)

        suggestion.reviewed_at = datetime.utcnow()
        suggestion.reviewed_by = 1  # TODO: Get from authenticated user

        await db.commit()

        logger.info(f"Suggestion {request.suggestion_id} {request.action}ed")

        return {"status": "success", "action": request.action}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling suggestion action: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to process suggestion action")


@router.post("/sessions/complete", response_model=SessionCompleteResponse)
async def complete_improvement_session(
    request: SessionCompleteRequest,
    db: AsyncSession = Depends(get_async_session),
    api_key: str = Security(get_api_key)
):
    """
    Complete an AI improvement session and apply accepted changes
    """
    try:
        # Get session
        session_query = select(AIImprovementSession).where(
            AIImprovementSession.id == request.session_id
        )
        session_result = await db.execute(session_query)
        session = session_result.scalar_one_or_none()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Get all accepted and modified suggestions
        suggestions_query = select(AISuggestion).where(
            AISuggestion.job_id == session.job_id,
            AISuggestion.status.in_(['accepted', 'modified'])
        )
        suggestions_result = await db.execute(suggestions_query)
        suggestions = suggestions_result.scalars().all()

        # Group suggestions by section
        sections_to_update = {}
        for sugg in suggestions:
            if sugg.section_id not in sections_to_update:
                sections_to_update[sugg.section_id] = []
            sections_to_update[sugg.section_id].append(sugg)

        # Apply improvements to sections
        for section_id, section_suggestions in sections_to_update.items():
            section_query = select(JobSection).where(JobSection.id == section_id)
            section_result = await db.execute(section_query)
            section = section_result.scalar_one_or_none()

            if section:
                # Reconstruct section with improvements
                sentences = section.section_content.split('. ')
                for sugg in sorted(section_suggestions, key=lambda x: x.sentence_index):
                    if sugg.sentence_index < len(sentences):
                        if sugg.status == 'accepted':
                            sentences[sugg.sentence_index] = sugg.suggested_text
                        elif sugg.status == 'modified' and sugg.modified_text:
                            sentences[sugg.sentence_index] = sugg.modified_text

                section.section_content = '. '.join(sentences)

        # Calculate quality score after improvements
        job_query = select(JobDescription).where(JobDescription.id == session.job_id)
        job_result = await db.execute(job_query)
        job = job_result.scalar_one_or_none()

        ai_service = AIImprovementService()
        quality_after = ai_service.calculate_quality_score(job.raw_content or "")

        # Update session
        session.session_end = datetime.utcnow()
        session.quality_score_after = quality_after

        # Calculate improvement percentage
        improvement_pct = 0.0
        if session.quality_score_before:
            improvement_pct = ((quality_after - float(session.quality_score_before)) /
                              float(session.quality_score_before)) * 100

        await db.commit()

        logger.info(f"Completed AI improvement session {request.session_id}")

        return SessionCompleteResponse(
            session_id=session.id,
            total_suggestions=session.total_suggestions,
            accepted_count=session.accepted_count,
            rejected_count=session.rejected_count,
            modified_count=session.modified_count,
            quality_score_after=quality_after,
            improvement_percentage=improvement_pct
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing session: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to complete improvement session")
```

**Register router in `backend/src/jd_ingestion/api/main.py`**:
```python
from jd_ingestion.api.endpoints import ai_improvement

app.include_router(ai_improvement.router, prefix="/api")
```

---

## Phase 2: Frontend UI Components (Week 2-3)

### 2.1 AI Improvement Context and State

**`src/contexts/AIImprovementContext.tsx`**
```typescript
import React, { createContext, useContext, useState, ReactNode } from 'react';

interface ImprovementSuggestion {
  id: number;
  sentenceIndex: number;
  originalText: string;
  suggestedText: string;
  rationale: string;
  suggestionType: string;
  confidenceScore: number;
  status: 'pending' | 'accepted' | 'rejected' | 'modified';
  modifiedText?: string;
}

interface ImprovementSession {
  sessionId: number;
  jobId: number;
  sectionsToImprove: number[];
  qualityScoreBefore: number;
}

interface ImprovementConfig {
  granularity: 'sentence' | 'clause' | 'paragraph';
  aggressiveness: 'conservative' | 'moderate' | 'aggressive';
  focusAreas: string[];
  autoAcceptThreshold?: number;
}

interface AIImprovementContextType {
  session: ImprovementSession | null;
  suggestions: Map<number, ImprovementSuggestion[]>; // sectionId -> suggestions
  currentSectionId: number | null;
  config: ImprovementConfig;

  startSession: (jobId: number, config: ImprovementConfig) => Promise<void>;
  analyzeSection: (sectionId: number) => Promise<void>;
  handleSuggestionAction: (
    suggestionId: number,
    action: 'accept' | 'reject' | 'modify',
    modifiedText?: string,
    feedback?: string
  ) => Promise<void>;
  completeSession: () => Promise<void>;
  setCurrentSectionId: (sectionId: number) => void;
}

const AIImprovementContext = createContext<AIImprovementContextType | undefined>(undefined);

export function AIImprovementProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<ImprovementSession | null>(null);
  const [suggestions, setSuggestions] = useState<Map<number, ImprovementSuggestion[]>>(new Map());
  const [currentSectionId, setCurrentSectionId] = useState<number | null>(null);
  const [config, setConfig] = useState<ImprovementConfig>({
    granularity: 'sentence',
    aggressiveness: 'moderate',
    focusAreas: ['clarity', 'professionalism'],
  });

  const startSession = async (jobId: number, improvementConfig: ImprovementConfig) => {
    // TODO: Call API to start session
    // const response = await apiClient.startImprovementSession(jobId, improvementConfig);
    // setSession(response);
    // setConfig(improvementConfig);
  };

  const analyzeSection = async (sectionId: number) => {
    if (!session) return;

    // TODO: Call API to analyze section
    // const response = await apiClient.analyzeSectionForImprovement(session.sessionId, sectionId);
    // setSuggestions(prev => new Map(prev).set(sectionId, response.suggestions));
  };

  const handleSuggestionAction = async (
    suggestionId: number,
    action: 'accept' | 'reject' | 'modify',
    modifiedText?: string,
    feedback?: string
  ) => {
    // TODO: Call API to handle action
    // await apiClient.handleSuggestionAction(suggestionId, action, modifiedText, feedback);

    // Update local state
    setSuggestions(prev => {
      const newMap = new Map(prev);
      for (const [sectionId, sectionSuggestions] of newMap.entries()) {
        const updatedSuggestions = sectionSuggestions.map(s =>
          s.id === suggestionId
            ? { ...s, status: action, modifiedText }
            : s
        );
        newMap.set(sectionId, updatedSuggestions);
      }
      return newMap;
    });
  };

  const completeSession = async () => {
    if (!session) return;

    // TODO: Call API to complete session
    // const response = await apiClient.completeImprovementSession(session.sessionId);
    // Reset state
    setSession(null);
    setSuggestions(new Map());
    setCurrentSectionId(null);
  };

  return (
    <AIImprovementContext.Provider
      value={{
        session,
        suggestions,
        currentSectionId,
        config,
        startSession,
        analyzeSection,
        handleSuggestionAction,
        completeSession,
        setCurrentSectionId,
      }}
    >
      {children}
    </AIImprovementContext.Provider>
  );
}

export function useAIImprovement() {
  const context = useContext(AIImprovementContext);
  if (!context) {
    throw new Error('useAIImprovement must be used within AIImprovementProvider');
  }
  return context;
}
```

### 2.2 AI Improvement Comparison View Component

**`src/components/ai/AIImprovementView.tsx`**
```typescript
import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Check, X, Edit, ChevronLeft, ChevronRight } from 'lucide-react';
import { useAIImprovement } from '@/contexts/AIImprovementContext';
import { cn } from '@/lib/utils';

interface AIImprovementViewProps {
  jobId: number;
  sections: Array<{ id: number; sectionType: string; content: string }>;
  onExit: () => void;
}

export function AIImprovementView({ jobId, sections, onExit }: AIImprovementViewProps) {
  const {
    session,
    suggestions,
    currentSectionId,
    config,
    startSession,
    analyzeSection,
    handleSuggestionAction,
    completeSession,
    setCurrentSectionId,
  } = useAIImprovement();

  const [isLoading, setIsLoading] = useState(false);
  const [editingSuggestionId, setEditingSuggestionId] = useState<number | null>(null);
  const [modifiedText, setModifiedText] = useState('');

  useEffect(() => {
    // Start session when component mounts
    if (!session) {
      startSession(jobId, config);
    }
  }, []);

  useEffect(() => {
    // Analyze current section when it changes
    if (currentSectionId && !suggestions.has(currentSectionId)) {
      setIsLoading(true);
      analyzeSection(currentSectionId).finally(() => setIsLoading(false));
    }
  }, [currentSectionId]);

  const currentSection = sections.find(s => s.id === currentSectionId);
  const currentSuggestions = currentSectionId ? suggestions.get(currentSectionId) || [] : [];

  const currentSectionIndex = sections.findIndex(s => s.id === currentSectionId);
  const canGoBack = currentSectionIndex > 0;
  const canGoForward = currentSectionIndex < sections.length - 1;

  const handlePreviousSection = () => {
    if (canGoBack) {
      setCurrentSectionId(sections[currentSectionIndex - 1].id);
    }
  };

  const handleNextSection = () => {
    if (canGoForward) {
      setCurrentSectionId(sections[currentSectionIndex + 1].id);
    }
  };

  const handleAccept = (suggestionId: number) => {
    handleSuggestionAction(suggestionId, 'accept');
  };

  const handleReject = (suggestionId: number) => {
    handleSuggestionAction(suggestionId, 'reject');
  };

  const handleModify = (suggestionId: number, suggestedText: string) => {
    setEditingSuggestionId(suggestionId);
    setModifiedText(suggestedText);
  };

  const handleApplyModification = (suggestionId: number) => {
    handleSuggestionAction(suggestionId, 'modify', modifiedText);
    setEditingSuggestionId(null);
    setModifiedText('');
  };

  const handleSaveAndExit = async () => {
    await completeSession();
    onExit();
  };

  return (
    <div className="fixed inset-0 bg-background z-50 overflow-auto">
      {/* Header */}
      <div className="border-b bg-card sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">AI Improvement Mode</h1>
            <p className="text-sm text-muted-foreground">
              Section: {currentSection?.sectionType || 'Select a section'}
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={onExit}>
              Exit Without Saving
            </Button>
            <Button onClick={handleSaveAndExit}>
              Save Improvements
            </Button>
          </div>
        </div>
      </div>

      {/* Section Navigation */}
      <div className="border-b bg-muted/50">
        <div className="container mx-auto px-4 py-2 flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={handlePreviousSection}
            disabled={!canGoBack}
          >
            <ChevronLeft className="w-4 h-4" />
            Previous
          </Button>

          <select
            className="flex-1 max-w-xs px-3 py-2 border rounded-md"
            value={currentSectionId || ''}
            onChange={(e) => setCurrentSectionId(Number(e.target.value))}
          >
            <option value="">Select Section</option>
            {sections.map(section => (
              <option key={section.id} value={section.id}>
                {section.sectionType}
              </option>
            ))}
          </select>

          <Button
            variant="ghost"
            size="sm"
            onClick={handleNextSection}
            disabled={!canGoForward}
          >
            Next
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Main Content - Split Panes */}
      <div className="container mx-auto px-4 py-6">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4" />
              <p className="text-muted-foreground">Analyzing section with AI...</p>
            </div>
          </div>
        ) : currentSuggestions.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-muted-foreground">
                No improvements suggested for this section. Content is already high-quality!
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-2 gap-6">
            {/* Original Content Pane */}
            <div>
              <h2 className="text-lg font-semibold mb-4">Original Content</h2>
              <div className="space-y-4">
                {currentSuggestions.map((suggestion) => (
                  <Card key={suggestion.id} className="border-l-4 border-l-muted">
                    <CardContent className="pt-4">
                      <p className="text-sm text-muted-foreground mb-2">
                        Sentence {suggestion.sentenceIndex + 1}
                      </p>
                      <p>{suggestion.originalText}</p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>

            {/* Improved Content Pane */}
            <div>
              <h2 className="text-lg font-semibold mb-4">AI-Improved Suggestions</h2>
              <div className="space-y-4">
                {currentSuggestions.map((suggestion) => (
                  <Card
                    key={suggestion.id}
                    className={cn(
                      'border-l-4 transition-colors',
                      suggestion.status === 'accepted' && 'border-l-green-500 bg-green-50',
                      suggestion.status === 'rejected' && 'border-l-red-500 bg-red-50',
                      suggestion.status === 'modified' && 'border-l-blue-500 bg-blue-50',
                      suggestion.status === 'pending' && 'border-l-yellow-500'
                    )}
                  >
                    <CardContent className="pt-4">
                      {editingSuggestionId === suggestion.id ? (
                        <div className="space-y-3">
                          <Textarea
                            value={modifiedText}
                            onChange={(e) => setModifiedText(e.target.value)}
                            className="min-h-[100px]"
                          />
                          <div className="flex gap-2">
                            <Button
                              size="sm"
                              onClick={() => handleApplyModification(suggestion.id)}
                            >
                              Apply Modification
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => setEditingSuggestionId(null)}
                            >
                              Cancel
                            </Button>
                          </div>
                        </div>
                      ) : (
                        <>
                          <p className={cn(
                            suggestion.status === 'rejected' && 'line-through text-muted-foreground'
                          )}>
                            {suggestion.status === 'modified'
                              ? suggestion.modifiedText
                              : suggestion.suggestedText}
                          </p>

                          <div className="mt-3 p-3 bg-muted rounded-md text-sm">
                            <p className="font-medium text-primary mb-1">
                              {suggestion.suggestionType.charAt(0).toUpperCase() +
                               suggestion.suggestionType.slice(1)} Improvement
                            </p>
                            <p className="text-muted-foreground">{suggestion.rationale}</p>
                            <p className="text-xs text-muted-foreground mt-1">
                              Confidence: {(suggestion.confidenceScore * 100).toFixed(0)}%
                            </p>
                          </div>

                          {suggestion.status === 'pending' && (
                            <div className="mt-3 flex gap-2">
                              <Button
                                size="sm"
                                variant="default"
                                onClick={() => handleAccept(suggestion.id)}
                                className="bg-green-600 hover:bg-green-700"
                              >
                                <Check className="w-4 h-4 mr-1" />
                                Accept
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleReject(suggestion.id)}
                                className="border-red-600 text-red-600 hover:bg-red-50"
                              >
                                <X className="w-4 h-4 mr-1" />
                                Reject
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleModify(suggestion.id, suggestion.suggestedText)}
                              >
                                <Edit className="w-4 h-4 mr-1" />
                                Modify
                              </Button>
                            </div>
                          )}

                          {suggestion.status !== 'pending' && (
                            <div className="mt-3 flex items-center gap-2 text-sm">
                              {suggestion.status === 'accepted' && (
                                <>
                                  <Check className="w-4 h-4 text-green-600" />
                                  <span className="text-green-600 font-medium">Accepted</span>
                                </>
                              )}
                              {suggestion.status === 'rejected' && (
                                <>
                                  <X className="w-4 h-4 text-red-600" />
                                  <span className="text-red-600 font-medium">Rejected</span>
                                </>
                              )}
                              {suggestion.status === 'modified' && (
                                <>
                                  <Edit className="w-4 h-4 text-blue-600" />
                                  <span className="text-blue-600 font-medium">Modified</span>
                                </>
                              )}
                            </div>
                          )}
                        </>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
```

### 2.3 Integration with Job Detail View

**Modify `src/components/jobs/JobDetailView.tsx`** to add AI Improvement button:

```typescript
import { AIImprovementView } from '@/components/ai/AIImprovementView';

// Add state
const [showAIImprovement, setShowAIImprovement] = useState(false);

// Add button in job detail header
<Button
  variant="outline"
  onClick={() => setShowAIImprovement(true)}
  disabled={!job || !job.sections || job.sections.length === 0}
>
  <Sparkles className="w-4 h-4 mr-2" />
  AI Improvement Mode
</Button>

// Render AI Improvement View when active
{showAIImprovement && job && (
  <AIImprovementView
    jobId={job.id}
    sections={job.sections}
    onExit={() => setShowAIImprovement(false)}
  />
)}
```

---

## Phase 3: Testing and Quality Assurance (Week 4)

### 3.1 Backend Tests

**`backend/tests/unit/test_ai_improvement_service.py`**
```python
import pytest
from jd_ingestion.services.ai_improvement_service import AIImprovementService

@pytest.mark.asyncio
async def test_analyze_section_generates_suggestions():
    service = AIImprovementService()

    section_content = """
    The incumbent is responsible for managing the team.
    Manages projects effectively.
    Ensures quality standards are met.
    """

    suggestions = await service.analyze_section(
        section_content=section_content,
        section_type="general_accountability",
        classification_level="EX-01",
        focus_areas=["clarity", "professionalism"],
        granularity="sentence",
        aggressiveness="moderate"
    )

    assert len(suggestions) > 0
    assert all(0 <= s.confidence_score <= 1 for s in suggestions)
    assert all(s.suggested_text != s.original_text for s in suggestions)

@pytest.mark.asyncio
async def test_quality_score_calculation():
    service = AIImprovementService()

    content = "The incumbent is accountable for strategic planning and execution."
    score = service.calculate_quality_score(content)

    assert 0 <= score <= 1
```

**`backend/tests/integration/test_ai_improvement_api.py`**
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_start_improvement_session(async_client: AsyncClient, test_job):
    response = await async_client.post(
        "/api/ai-improvement/sessions/start",
        json={
            "job_id": test_job.id,
            "configuration": {
                "granularity": "sentence",
                "aggressiveness": "moderate",
                "focus_areas": ["clarity", "professionalism"]
            }
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == test_job.id
    assert "session_id" in data
    assert "quality_score_before" in data

@pytest.mark.asyncio
async def test_analyze_section_returns_suggestions(async_client: AsyncClient, test_session, test_section):
    response = await async_client.post(
        "/api/ai-improvement/sections/analyze",
        json={
            "session_id": test_session.id,
            "section_id": test_section.id
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "suggestions" in data
    assert data["section_id"] == test_section.id
```

### 3.2 Frontend Tests

**`src/components/ai/__tests__/AIImprovementView.test.tsx`**
```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AIImprovementView } from '../AIImprovementView';
import { AIImprovementProvider } from '@/contexts/AIImprovementContext';

describe('AIImprovementView', () => {
  const mockSections = [
    { id: 1, sectionType: 'General Accountability', content: 'Test content' }
  ];

  it('should render comparison panes', () => {
    render(
      <AIImprovementProvider>
        <AIImprovementView
          jobId={1}
          sections={mockSections}
          onExit={() => {}}
        />
      </AIImprovementProvider>
    );

    expect(screen.getByText('Original Content')).toBeInTheDocument();
    expect(screen.getByText('AI-Improved Suggestions')).toBeInTheDocument();
  });

  it('should handle accept suggestion action', async () => {
    render(
      <AIImprovementProvider>
        <AIImprovementView
          jobId={1}
          sections={mockSections}
          onExit={() => {}}
        />
      </AIImprovementProvider>
    );

    const acceptButton = screen.getByText('Accept');
    fireEvent.click(acceptButton);

    await waitFor(() => {
      expect(screen.getByText('Accepted')).toBeInTheDocument();
    });
  });
});
```

---

## Phase 4: Documentation and Deployment (Week 4)

### 4.1 API Documentation

Update Swagger/OpenAPI documentation with new endpoints

### 4.2 User Training

Create training materials for advisors on using AI improvement mode

### 4.3 Deployment Checklist

- [ ] Run database migrations
- [ ] Configure OpenAI API key in environment
- [ ] Deploy backend changes
- [ ] Deploy frontend changes
- [ ] Run smoke tests
- [ ] Monitor AI API usage and costs
- [ ] Gather user feedback

---

## Success Metrics

- **Acceptance Rate**: Target >60% of AI suggestions accepted or modified
- **Time Savings**: Target 30% reduction in job description improvement time
- **Quality Improvement**: Target 15-20% increase in quality scores
- **User Satisfaction**: Target >4.0/5 rating from advisors
- **API Performance**: <10 seconds for AI analysis per section

---

## Future Enhancements

1. **Custom AI Models**: Train organization-specific models for better suggestions
2. **Batch Processing**: Improve multiple jobs simultaneously
3. **Collaborative Improvement**: Multiple advisors reviewing AI suggestions together
4. **Version Comparison**: Compare AI-improved versions with originals
5. **Automated Quality Scoring**: More sophisticated readability and completeness metrics
