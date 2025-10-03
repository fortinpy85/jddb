"""
AI Suggestions API Endpoints for Phase 2.

This module provides endpoints for:
- Text enhancement suggestions
- Grammar and style improvements
- Bias detection and inclusivity analysis
- Treasury Board compliance checking
- Smart template generation
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from ...database.connection import get_async_session
from ...services.ai_enhancement_service import AIEnhancementService
from ...utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/ai", tags=["ai-suggestions"])


class TextSuggestionRequest(BaseModel):
    """Request model for text improvement suggestions."""

    text: str = Field(
        ..., min_length=1, max_length=10000, description="Text to analyze"
    )
    context: Optional[str] = Field(
        None, description="Additional context for suggestions"
    )
    suggestion_types: List[str] = Field(
        default=["grammar", "style", "clarity"],
        description="Types of suggestions to generate",
    )


class Suggestion(BaseModel):
    """Model for a single suggestion."""

    id: str
    type: str  # grammar, style, clarity, bias, compliance
    original_text: str
    suggested_text: str
    explanation: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    start_index: int
    end_index: int


class SuggestionsResponse(BaseModel):
    """Response model for text suggestions."""

    suggestions: List[Suggestion]
    overall_score: float = Field(..., ge=0.0, le=1.0)
    processing_time_ms: float


class ComplianceCheckRequest(BaseModel):
    """Request model for compliance checking."""

    text: str = Field(..., min_length=1, max_length=10000)
    compliance_frameworks: List[str] = Field(
        default=["treasury_board", "accessibility", "bilingual"],
        description="Compliance frameworks to check against",
    )


class ComplianceIssue(BaseModel):
    """Model for a compliance issue."""

    framework: str
    issue_type: str
    description: str
    severity: str  # high, medium, low
    location: Optional[str] = None
    recommendation: str


class ComplianceResponse(BaseModel):
    """Response model for compliance check."""

    compliant: bool
    issues: List[ComplianceIssue]
    compliance_score: float = Field(..., ge=0.0, le=1.0)


class BiasAnalysisRequest(BaseModel):
    """Request model for bias analysis."""

    text: str = Field(..., min_length=1, max_length=10000)
    analysis_types: List[str] = Field(
        default=["gender", "age", "disability", "cultural"],
        description="Types of bias to analyze",
    )


class BiasIssue(BaseModel):
    """Model for a bias issue."""

    type: str
    description: str
    problematic_text: str
    suggested_alternatives: List[str]
    severity: str
    start_index: int
    end_index: int


class BiasAnalysisResponse(BaseModel):
    """Response model for bias analysis."""

    bias_free: bool
    issues: List[BiasIssue]
    inclusivity_score: float = Field(..., ge=0.0, le=1.0)


class TemplateRequest(BaseModel):
    """Request model for template generation."""

    classification: str = Field(
        ..., description="Job classification (e.g., EX-01, EC-05)"
    )
    language: str = Field(default="en", description="Language (en or fr)")
    custom_requirements: Optional[Dict[str, Any]] = Field(
        None, description="Custom requirements for template"
    )


class TemplateResponse(BaseModel):
    """Response model for template generation."""

    template_id: str
    classification: str
    language: str
    sections: Dict[str, str]
    metadata: Dict[str, Any]


@router.post("/suggest-improvements", response_model=SuggestionsResponse)
async def suggest_improvements(
    request: TextSuggestionRequest,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Generate AI-powered text improvement suggestions.

    Analyzes text and provides suggestions for:
    - Grammar corrections
    - Style improvements
    - Clarity enhancements
    - Tone adjustments
    """
    try:
        start_time = datetime.utcnow()

        service = AIEnhancementService(db)
        suggestions = await service.generate_suggestions(
            text=request.text,
            context=request.context,
            suggestion_types=request.suggestion_types,
        )

        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        return SuggestionsResponse(
            suggestions=suggestions["suggestions"],
            overall_score=suggestions["overall_score"],
            processing_time_ms=processing_time,
        )

    except Exception as e:
        logger.error(f"Error generating suggestions: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate suggestions")


@router.post("/check-compliance", response_model=ComplianceResponse)
async def check_compliance(
    request: ComplianceCheckRequest,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Check text compliance against government policies and standards.

    Validates against:
    - Treasury Board directives
    - Accessibility standards (WCAG)
    - Official languages requirements
    """
    try:
        service = AIEnhancementService(db)
        compliance_result = await service.check_compliance(
            text=request.text,
            frameworks=request.compliance_frameworks,
        )

        return ComplianceResponse(
            compliant=compliance_result["compliant"],
            issues=compliance_result["issues"],
            compliance_score=compliance_result["compliance_score"],
        )

    except Exception as e:
        logger.error(f"Error checking compliance: {e}")
        raise HTTPException(status_code=500, detail="Failed to check compliance")


@router.post("/analyze-bias", response_model=BiasAnalysisResponse)
async def analyze_bias(
    request: BiasAnalysisRequest,
    use_gpt4: bool = True,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Analyze text for bias and inclusivity issues.

    Detects potential bias related to:
    - Gender
    - Age
    - Disability
    - Cultural background
    - Other protected characteristics

    Query Parameters:
    - use_gpt4: Enable GPT-4 context-aware bias detection (default: True)
      Set to False for faster, pattern-only analysis
    """
    try:
        service = AIEnhancementService(db)
        bias_result = await service.analyze_bias(
            text=request.text,
            analysis_types=request.analysis_types,
            use_gpt4=use_gpt4,
        )

        logger.info(f"Bias analysis result: {len(bias_result['issues'])} issues found")
        logger.info(
            f"Analysis types: {request.analysis_types}, GPT-4 enhanced: {use_gpt4}"
        )
        logger.info(f"Text analyzed: {request.text[:100]}")

        return BiasAnalysisResponse(
            bias_free=bias_result["bias_free"],
            issues=bias_result["issues"],
            inclusivity_score=bias_result["inclusivity_score"],
        )

    except Exception as e:
        logger.error(f"Error analyzing bias: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze bias")


@router.get("/templates/{classification}", response_model=TemplateResponse)
async def get_template(
    classification: str,
    language: str = "en",
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get AI-generated job description template for a classification.

    Returns a structured template with:
    - Standard sections for the classification
    - Language-appropriate content
    - Compliance with government standards
    """
    try:
        service = AIEnhancementService(db)
        template = await service.generate_template(
            classification=classification,
            language=language,
        )

        return TemplateResponse(
            template_id=template["template_id"],
            classification=template["classification"],
            language=template["language"],
            sections=template["sections"],
            metadata=template["metadata"],
        )

    except Exception as e:
        logger.error(f"Error generating template: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate template")


@router.post("/templates/generate", response_model=TemplateResponse)
async def generate_custom_template(
    request: TemplateRequest,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Generate a custom job description template with specific requirements.

    Allows customization of:
    - Section content
    - Competency requirements
    - Language style and formality
    """
    try:
        service = AIEnhancementService(db)
        template = await service.generate_template(
            classification=request.classification,
            language=request.language,
            custom_requirements=request.custom_requirements,
        )

        return TemplateResponse(
            template_id=template["template_id"],
            classification=template["classification"],
            language=template["language"],
            sections=template["sections"],
            metadata=template["metadata"],
        )

    except Exception as e:
        logger.error(f"Error generating custom template: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate template")


# Phase 3: Quality Scoring Endpoints


class QualityScoreRequest(BaseModel):
    """Request model for quality scoring."""

    job_data: Dict[str, Any] = Field(..., description="Complete job description data")


class QualityDimensionScore(BaseModel):
    """Model for individual quality dimension score."""

    score: float = Field(..., ge=0.0, le=100.0)
    weight: str
    details: Dict[str, Any]


class QualityScoreResponse(BaseModel):
    """Response model for comprehensive quality scoring."""

    overall_score: float = Field(..., ge=0.0, le=100.0)
    quality_level: str  # Excellent, Good, Fair, Needs Improvement
    quality_color: str  # green, blue, yellow, red
    dimension_scores: Dict[str, QualityDimensionScore]
    top_recommendations: List[str]
    improvement_priority: List[str]


@router.post("/quality-score", response_model=QualityScoreResponse)
async def calculate_quality_score(
    request: QualityScoreRequest,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Calculate comprehensive quality score for a job description.

    Analyzes multiple quality dimensions:
    - Readability (20%): Flesch-Kincaid grade level, reading ease
    - Completeness (25%): Required sections present with adequate content
    - Clarity (15%): Sentence structure, paragraph organization
    - Inclusivity (20%): Bias-free, inclusive language
    - Compliance (20%): Government standards adherence

    Returns overall score (0-100) with detailed breakdown.
    """
    try:
        start_time = datetime.utcnow()

        service = AIEnhancementService(db)
        quality_assessment = await service.calculate_comprehensive_quality_score(
            job_data=request.job_data
        )

        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.info(
            f"Quality score calculated in {processing_time:.2f}ms: {quality_assessment['overall_score']}"
        )

        return QualityScoreResponse(**quality_assessment)

    except Exception as e:
        logger.error(f"Error calculating quality score: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to calculate quality score: {str(e)}"
        )


# Phase 3: Content Generation Endpoints


@router.get("/test-endpoint")
async def test_new_endpoint():
    """Simple test endpoint to verify registration works."""
    return {"status": "success", "message": "Test endpoint is working"}


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
