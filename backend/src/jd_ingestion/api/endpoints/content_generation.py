"""
Content Generation API Endpoints for Phase 3.

This module provides GPT-4 powered content generation endpoints:
- Section auto-completion
- Content enhancement (clarity, active voice, conciseness)
- Inline writing suggestions
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from ...database.connection import get_async_session
from ...services.ai_enhancement_service import AIEnhancementService
from ...utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/ai/content", tags=["content-generation"])


# Request/Response Models


class SectionCompletionRequest(BaseModel):
    """Request model for section auto-completion."""

    section_type: str = Field(..., description="Type of section to complete")
    partial_content: str = Field(
        ..., description="Existing partial content to complete"
    )
    classification: str = Field(..., description="Job classification (e.g., EX-01)")
    language: str = Field(default="en", description="Language (en or fr)")
    context: Optional[Dict[str, Any]] = Field(
        None, description="Additional context (department, reporting_to, etc.)"
    )


class SectionCompletionResponse(BaseModel):
    """Response model for section completion."""

    completed_content: str
    completion_text: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    message: str


class ContentEnhancementRequest(BaseModel):
    """Request model for content enhancement."""

    text: str = Field(..., min_length=1, max_length=5000)
    enhancement_types: List[str] = Field(
        default=["clarity", "active_voice"],
        description="Types: clarity, active_voice, conciseness, formality, bias_free",
    )
    language: str = Field(default="en", description="Language")


class ContentEnhancementResponse(BaseModel):
    """Response model for content enhancement."""

    enhanced_text: str
    original_text: str
    changes: List[str]
    enhancement_types: List[str]
    message: str


class InlineSuggestionsRequest(BaseModel):
    """Request model for inline suggestions."""

    text: str = Field(..., min_length=1, max_length=5000)
    cursor_position: int = Field(..., ge=0)
    context: Optional[str] = Field(None, description="Additional context")


class InlineSuggestion(BaseModel):
    """Model for an inline suggestion."""

    text: str
    reason: str


class InlineSuggestionsResponse(BaseModel):
    """Response model for inline suggestions."""

    suggestions: List[InlineSuggestion]
    cursor_position: int
    message: str


# API Endpoints


@router.post("/complete-section", response_model=SectionCompletionResponse)
async def complete_section(
    request: SectionCompletionRequest,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Auto-complete a job description section using GPT-4.

    Intelligently completes partial content while maintaining:
    - Consistent tone and style
    - Government/professional language
    - Treasury Board standards
    - Bilingual capability
    """
    try:
        service = AIEnhancementService(db)
        result = await service.complete_section(
            section_type=request.section_type,
            partial_content=request.partial_content,
            classification=request.classification,
            language=request.language,
            context=request.context,
        )

        logger.info(
            f"Section completion: {request.section_type} for {request.classification}"
        )

        return SectionCompletionResponse(**result)

    except Exception as e:
        logger.error(f"Error completing section: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to complete section: {str(e)}"
        )


@router.post("/enhance-content", response_model=ContentEnhancementResponse)
async def enhance_content(
    request: ContentEnhancementRequest,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Enhance job description content for clarity, active voice, and professionalism.

    Enhancement types available:
    - **clarity**: Simplify complex sentences
    - **active_voice**: Convert passive to active voice
    - **conciseness**: Remove redundancy and wordiness
    - **formality**: Adjust tone for government standards
    - **bias_free**: Remove biased or non-inclusive language
    """
    try:
        service = AIEnhancementService(db)
        result = await service.enhance_content(
            text=request.text,
            enhancement_types=request.enhancement_types,
            language=request.language,
        )

        logger.info(
            f"Content enhanced with {len(result.get('changes', []))} changes ({request.enhancement_types})"
        )

        return ContentEnhancementResponse(**result)

    except Exception as e:
        logger.error(f"Error enhancing content: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to enhance content: {str(e)}"
        )


@router.post("/inline-suggestions", response_model=InlineSuggestionsResponse)
async def get_inline_suggestions(
    request: InlineSuggestionsRequest,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Generate smart inline writing suggestions based on cursor position.

    Provides context-aware suggestions for:
    - Sentence completion
    - Common patterns in job descriptions
    - Professional phrasing
    - Government writing standards
    """
    try:
        service = AIEnhancementService(db)
        result = await service.generate_inline_suggestions(
            text=request.text,
            cursor_position=request.cursor_position,
            context=request.context,
        )

        logger.info(
            f"Generated {len(result.get('suggestions', []))} inline suggestions"
        )

        return InlineSuggestionsResponse(**result)

    except Exception as e:
        logger.error(f"Error generating inline suggestions: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate suggestions: {str(e)}"
        )
