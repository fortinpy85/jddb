"""
Translation Quality API Endpoints

FastAPI endpoints for translation quality assessment and validation.
"""

import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...services.translation_quality_service import TranslationQualityService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/translation-quality", tags=["translation-quality"])

# Initialize service
quality_service = TranslationQualityService()


# Pydantic Models
class TranslationAssessmentRequest(BaseModel):
    english_text: str = Field(..., description="Source English text")
    french_text: str = Field(..., description="Target French text")
    context: Dict[str, Any] = Field(default={}, description="Additional context")


class TranslationValidationRequest(BaseModel):
    segment_id: str = Field(..., description="Segment identifier")
    english_text: str = Field(..., description="Source text")
    french_text: str = Field(..., description="Translation text")


class DocumentSegment(BaseModel):
    id: str = Field(..., description="Segment ID")
    english: str = Field(..., description="English content")
    french: str = Field(..., description="French content")


class ConsistencyCheckRequest(BaseModel):
    segments: List[DocumentSegment] = Field(..., description="Document segments")


@router.post("/assess", response_model=Dict[str, Any])
async def assess_translation_quality(request: TranslationAssessmentRequest):
    """
    Assess overall translation quality.

    Provides comprehensive quality scoring including:
    - Completeness check
    - Length ratio analysis
    - Terminology consistency
    - Formatting validation

    Returns quality score (0-100) with detailed breakdown.
    """
    try:
        assessment = await quality_service.assess_translation_quality(
            english_text=request.english_text,
            french_text=request.french_text,
            context=request.context,
        )

        return {
            "success": True,
            "assessment": assessment,
        }

    except Exception as e:
        logger.error(f"Error assessing translation quality: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to assess translation quality: {str(e)}",
        )


@router.post("/validate", response_model=Dict[str, Any])
async def validate_translation(request: TranslationValidationRequest):
    """
    Validate a single translation segment.

    Determines if translation meets quality standards and
    provides pass/fail status with recommendations.
    """
    try:
        validation = await quality_service.validate_translation(
            segment_id=request.segment_id,
            english_text=request.english_text,
            french_text=request.french_text,
        )

        return {
            "success": True,
            "validation": validation,
        }

    except Exception as e:
        logger.error(f"Error validating translation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate translation: {str(e)}",
        )


@router.post("/consistency", response_model=Dict[str, Any])
async def check_document_consistency(request: ConsistencyCheckRequest):
    """
    Check consistency across all document segments.

    Analyzes terminology usage and identifies inconsistencies
    in translation across multiple segments.
    """
    try:
        segments_data = [seg.dict() for seg in request.segments]

        consistency = await quality_service.check_document_consistency(
            segments=segments_data
        )

        return {
            "success": True,
            "consistency": consistency,
        }

    except Exception as e:
        logger.error(f"Error checking document consistency: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check consistency: {str(e)}",
        )


@router.post("/suggestions", response_model=Dict[str, Any])
async def get_improvement_suggestions(request: TranslationAssessmentRequest):
    """
    Get suggestions for improving translation quality.

    Provides actionable recommendations for:
    - Terminology improvements
    - Length adjustments
    - Completeness issues
    """
    try:
        suggestions = await quality_service.suggest_improvements(
            english_text=request.english_text,
            french_text=request.french_text,
        )

        return {
            "success": True,
            "suggestions": suggestions,
            "count": len(suggestions),
        }

    except Exception as e:
        logger.error(f"Error generating suggestions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate suggestions: {str(e)}",
        )


@router.get("/terminology", response_model=Dict[str, Any])
async def get_terminology_glossary():
    """
    Get standard government terminology glossary.

    Returns approved translations for common government terms.
    """
    try:
        return {
            "success": True,
            "glossary": {
                "english_to_french": quality_service.GOVERNMENT_TERMINOLOGY["en"],
                "french_to_english": quality_service.GOVERNMENT_TERMINOLOGY["fr"],
            },
            "count": len(quality_service.GOVERNMENT_TERMINOLOGY["en"]),
        }

    except Exception as e:
        logger.error(f"Error fetching terminology: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch terminology: {str(e)}",
        )
