"""
Translation Memory API Endpoints

FastAPI endpoints for managing translation memory and providing
translation suggestions using pgvector similarity search.
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ...database.connection import get_db
from ...services.translation_memory_service import TranslationMemoryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/translation-memory", tags=["translation-memory"])


# Pydantic Models
class CreateProjectRequest(BaseModel):
    name: str = Field(..., description="Project name", max_length=255)
    description: Optional[str] = Field(None, description="Project description")
    source_language: str = Field(..., description="Source language code (e.g., 'en')", max_length=5)
    target_language: str = Field(..., description="Target language code (e.g., 'fr')", max_length=5)
    project_type: str = Field("job_descriptions", description="Type of project")


class AddTranslationRequest(BaseModel):
    source_text: str = Field(..., description="Source text to translate")
    target_text: str = Field(..., description="Target translation")
    source_language: str = Field(..., description="Source language code", max_length=5)
    target_language: str = Field(..., description="Target language code", max_length=5)
    domain: Optional[str] = Field(None, description="Domain category", max_length=50)
    subdomain: Optional[str] = Field(None, description="Subdomain category", max_length=50)
    quality_score: Optional[float] = Field(None, description="Quality score (0-1)", ge=0, le=1)
    confidence_score: Optional[float] = Field(None, description="Confidence score (0-1)", ge=0, le=1)
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class TranslationSuggestionRequest(BaseModel):
    source_text: str = Field(..., description="Text to find suggestions for")
    source_language: str = Field(..., description="Source language code", max_length=5)
    target_language: str = Field(..., description="Target language code", max_length=5)
    project_id: Optional[int] = Field(None, description="Limit to specific project")
    context: Optional[str] = Field(None, description="Additional context")


class UpdateUsageRequest(BaseModel):
    used_translation: bool = Field(True, description="Whether the translation was used")
    user_feedback: Optional[Dict[str, Any]] = Field(None, description="User feedback")


# Initialize service
tm_service = TranslationMemoryService()


@router.post("/projects", response_model=Dict[str, Any])
async def create_project(
    request: CreateProjectRequest,
    db: Session = Depends(get_db)
):
    """Create a new translation project."""
    try:
        project = tm_service.create_project(
            name=request.name,
            description=request.description,
            source_language=request.source_language,
            target_language=request.target_language,
            project_type=request.project_type,
            db=db
        )

        return {
            "success": True,
            "message": "Translation project created successfully",
            "project": {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "source_language": project.source_language,
                "target_language": project.target_language,
                "project_type": project.project_type,
                "status": project.status,
                "created_at": project.created_at.isoformat()
            }
        }

    except Exception as e:
        logger.error(f"Error creating translation project: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create translation project: {str(e)}"
        )


@router.get("/projects", response_model=Dict[str, Any])
async def list_projects(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
    db: Session = Depends(get_db)
):
    """List translation projects with pagination."""
    try:
        from ...database.models import TranslationProject

        query = db.query(TranslationProject)
        total = query.count()

        projects = query.offset(skip).limit(limit).all()

        return {
            "success": True,
            "total": total,
            "skip": skip,
            "limit": limit,
            "projects": [
                {
                    "id": project.id,
                    "name": project.name,
                    "description": project.description,
                    "source_language": project.source_language,
                    "target_language": project.target_language,
                    "project_type": project.project_type,
                    "status": project.status,
                    "created_at": project.created_at.isoformat()
                }
                for project in projects
            ]
        }

    except Exception as e:
        logger.error(f"Error listing translation projects: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list translation projects: {str(e)}"
        )


@router.post("/projects/{project_id}/translations", response_model=Dict[str, Any])
async def add_translation(
    project_id: int = Path(..., description="Project ID"),
    request: AddTranslationRequest = ...,
    db: Session = Depends(get_db)
):
    """Add a new translation to the memory."""
    try:
        tm_entry = tm_service.add_translation_memory(
            project_id=project_id,
            source_text=request.source_text,
            target_text=request.target_text,
            source_language=request.source_language,
            target_language=request.target_language,
            domain=request.domain,
            subdomain=request.subdomain,
            quality_score=request.quality_score,
            confidence_score=request.confidence_score,
            metadata=request.metadata,
            db=db
        )

        return {
            "success": True,
            "message": "Translation added to memory successfully",
            "translation": {
                "id": tm_entry.id,
                "source_text": tm_entry.source_text,
                "target_text": tm_entry.target_text,
                "source_language": tm_entry.source_language,
                "target_language": tm_entry.target_language,
                "domain": tm_entry.domain,
                "subdomain": tm_entry.subdomain,
                "quality_score": float(tm_entry.quality_score) if tm_entry.quality_score else None,
                "confidence_score": float(tm_entry.confidence_score) if tm_entry.confidence_score else None,
                "usage_count": tm_entry.usage_count,
                "created_at": tm_entry.created_at.isoformat()
            }
        }

    except Exception as e:
        logger.error(f"Error adding translation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add translation: {str(e)}"
        )


@router.post("/suggestions", response_model=Dict[str, Any])
async def get_translation_suggestions(
    request: TranslationSuggestionRequest,
    db: Session = Depends(get_db)
):
    """Get translation suggestions based on similarity search."""
    try:
        suggestions = tm_service.get_translation_suggestions(
            source_text=request.source_text,
            source_language=request.source_language,
            target_language=request.target_language,
            project_id=request.project_id,
            context=request.context,
            db=db
        )

        return {
            "success": True,
            "query": {
                "source_text": request.source_text,
                "source_language": request.source_language,
                "target_language": request.target_language,
                "project_id": request.project_id
            },
            "suggestions": suggestions,
            "count": len(suggestions)
        }

    except Exception as e:
        logger.error(f"Error getting translation suggestions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get translation suggestions: {str(e)}"
        )


@router.post("/search", response_model=Dict[str, Any])
async def search_similar_translations(
    query_text: str = Query(..., description="Text to search for"),
    source_language: str = Query(..., description="Source language code"),
    target_language: str = Query(..., description="Target language code"),
    project_id: Optional[int] = Query(None, description="Limit to specific project"),
    similarity_threshold: float = Query(0.7, ge=0, le=1, description="Minimum similarity score"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    db: Session = Depends(get_db)
):
    """Search for similar translations using vector similarity."""
    try:
        results = tm_service.search_similar_translations(
            query_text=query_text,
            source_language=source_language,
            target_language=target_language,
            project_id=project_id,
            similarity_threshold=similarity_threshold,
            limit=limit,
            db=db
        )

        return {
            "success": True,
            "query": {
                "text": query_text,
                "source_language": source_language,
                "target_language": target_language,
                "similarity_threshold": similarity_threshold,
                "project_id": project_id
            },
            "results": results,
            "count": len(results)
        }

    except Exception as e:
        logger.error(f"Error searching similar translations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search similar translations: {str(e)}"
        )


@router.put("/translations/{tm_id}/usage", response_model=Dict[str, Any])
async def update_translation_usage(
    tm_id: int = Path(..., description="Translation memory ID"),
    request: UpdateUsageRequest = ...,
    db: Session = Depends(get_db)
):
    """Update usage statistics for a translation memory entry."""
    try:
        tm_service.update_usage_stats(
            tm_id=tm_id,
            used_translation=request.used_translation,
            user_feedback=request.user_feedback,
            db=db
        )

        return {
            "success": True,
            "message": "Translation usage updated successfully",
            "translation_id": tm_id
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating translation usage: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update translation usage: {str(e)}"
        )


@router.get("/projects/{project_id}/statistics", response_model=Dict[str, Any])
async def get_project_statistics(
    project_id: int = Path(..., description="Project ID"),
    db: Session = Depends(get_db)
):
    """Get statistics for a translation project."""
    try:
        stats = tm_service.get_project_statistics(project_id=project_id, db=db)

        return {
            "success": True,
            "statistics": stats
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting project statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get project statistics: {str(e)}"
        )


@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Health check endpoint for translation memory service."""
    return {
        "success": True,
        "service": "Translation Memory",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "Project Management",
            "Translation Storage",
            "Vector Similarity Search",
            "Usage Tracking",
            "Statistics"
        ]
    }