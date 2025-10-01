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

    text: str = Field(..., min_length=1, max_length=10000, description="Text to analyze")
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

    classification: str = Field(..., description="Job classification (e.g., EX-01, EC-05)")
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
    """
    try:
        service = AIEnhancementService(db)
        bias_result = await service.analyze_bias(
            text=request.text,
            analysis_types=request.analysis_types,
        )

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