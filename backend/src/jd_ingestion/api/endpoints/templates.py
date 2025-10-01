"""
Template API Endpoints

FastAPI endpoints for job description template generation and management.
"""

import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ...services.template_generation_service import TemplateGenerationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/templates", tags=["templates"])

# Initialize service
template_service = TemplateGenerationService()


# Pydantic Models
class TemplateRequest(BaseModel):
    classification: str = Field(..., description="Job classification (e.g., 'EX', 'EC')")
    level: Optional[str] = Field(None, description="Classification level (e.g., '01', '02')")
    language: str = Field("en", description="Template language (en or fr)")


class CustomizationRequest(BaseModel):
    template: Dict[str, Any] = Field(..., description="Base template")
    customizations: Dict[str, str] = Field(..., description="Placeholder replacements")


class VariationRequest(BaseModel):
    template: Dict[str, Any] = Field(..., description="Base template")
    count: int = Field(3, ge=1, le=5, description="Number of variations")


@router.get("/classifications", response_model=List[Dict[str, str]])
async def get_classifications():
    """Get list of available job classifications."""
    try:
        classifications = template_service.get_available_classifications()
        return classifications
    except Exception as e:
        logger.error(f"Error getting classifications: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get classifications: {str(e)}"
        )


@router.post("/generate", response_model=Dict[str, Any])
async def generate_template(request: TemplateRequest):
    """
    Generate a job description template for a specific classification.

    Args:
        request: Template generation parameters

    Returns:
        Generated template with sections and placeholders
    """
    try:
        template = await template_service.get_template_by_classification(
            classification=request.classification,
            language=request.language,
            level=request.level,
        )

        return {
            "success": True,
            "template": template,
        }

    except Exception as e:
        logger.error(f"Error generating template: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate template: {str(e)}"
        )


@router.get("/generate/{classification}", response_model=Dict[str, Any])
async def generate_template_by_classification(
    classification: str,
    level: Optional[str] = Query(None, description="Classification level"),
    language: str = Query("en", description="Template language (en or fr)"),
):
    """
    Generate a template using path parameter for classification.

    Args:
        classification: Job classification code
        level: Optional classification level
        language: Template language

    Returns:
        Generated template
    """
    try:
        template = await template_service.get_template_by_classification(
            classification=classification.upper(),
            language=language,
            level=level,
        )

        return {
            "success": True,
            "template": template,
        }

    except Exception as e:
        logger.error(f"Error generating template: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate template: {str(e)}"
        )


@router.post("/customize", response_model=Dict[str, Any])
async def customize_template(request: CustomizationRequest):
    """
    Customize a template by replacing placeholders with actual content.

    Args:
        request: Template and customization values

    Returns:
        Customized template
    """
    try:
        customized = await template_service.customize_template(
            template=request.template,
            customizations=request.customizations,
        )

        return {
            "success": True,
            "template": customized,
            "customizations_applied": len(request.customizations),
        }

    except Exception as e:
        logger.error(f"Error customizing template: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to customize template: {str(e)}"
        )


@router.post("/variations", response_model=Dict[str, Any])
async def generate_variations(request: VariationRequest):
    """
    Generate multiple variations of a template.

    Args:
        request: Base template and variation count

    Returns:
        List of template variations
    """
    try:
        variations = await template_service.generate_template_variations(
            base_template=request.template,
            variation_count=request.count,
        )

        return {
            "success": True,
            "variations": variations,
            "count": len(variations),
        }

    except Exception as e:
        logger.error(f"Error generating variations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate variations: {str(e)}"
        )


@router.post("/placeholders", response_model=Dict[str, Any])
async def extract_placeholders(template: Dict[str, Any]):
    """
    Extract all placeholders from a template.

    Args:
        template: Template to analyze

    Returns:
        List of placeholders
    """
    try:
        placeholders = await template_service.extract_placeholders(template)

        return {
            "success": True,
            "placeholders": placeholders,
            "count": len(placeholders),
        }

    except Exception as e:
        logger.error(f"Error extracting placeholders: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract placeholders: {str(e)}"
        )


@router.post("/validate", response_model=Dict[str, Any])
async def validate_template(template: Dict[str, Any]):
    """
    Validate template structure and content.

    Args:
        template: Template to validate

    Returns:
        Validation results
    """
    try:
        validation = await template_service.validate_template(template)

        return {
            "success": True,
            "validation": validation,
        }

    except Exception as e:
        logger.error(f"Error validating template: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate template: {str(e)}"
        )


@router.get("/bilingual/{classification}", response_model=Dict[str, Any])
async def get_bilingual_template(
    classification: str,
    level: Optional[str] = Query(None, description="Classification level"),
):
    """
    Get both English and French versions of a template.

    Args:
        classification: Job classification code
        level: Optional classification level

    Returns:
        Dictionary with both language versions
    """
    try:
        bilingual = await template_service.get_bilingual_template(
            classification=classification.upper(),
            level=level,
        )

        return {
            "success": True,
            "template": bilingual,
        }

    except Exception as e:
        logger.error(f"Error generating bilingual template: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate bilingual template: {str(e)}"
        )