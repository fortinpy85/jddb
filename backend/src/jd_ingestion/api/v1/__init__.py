"""
API Version 1

This module provides versioned API routing for future-proofing.
"""

from fastapi import APIRouter
from ..endpoints import (
    ai_suggestions,
    analysis,
    analytics,
    auth,
    bilingual_documents,
    content_generation,
    health,
    ingestion,
    jobs,
    performance,
    phase2_monitoring,
    preferences,
    quality,
    rate_limits,
    rlhf,
    saved_searches,
    search,
    tasks,
    templates,
    translation_memory,
    translation_quality,
    websocket,
)

# Create v1 router
v1_router = APIRouter(prefix="/v1")

# Include all endpoint routers under v1
v1_router.include_router(ingestion.router, prefix="/ingestion", tags=["v1-ingestion"])
v1_router.include_router(jobs.router, prefix="/jobs", tags=["v1-jobs"])
v1_router.include_router(search.router, prefix="/search", tags=["v1-search"])
v1_router.include_router(tasks.router, prefix="/tasks", tags=["v1-tasks"])
v1_router.include_router(analysis.router, prefix="/analysis", tags=["v1-analysis"])
v1_router.include_router(quality.router, prefix="/quality", tags=["v1-quality"])
v1_router.include_router(analytics.router, prefix="/analytics", tags=["v1-analytics"])
v1_router.include_router(
    performance.router, prefix="/performance", tags=["v1-performance"]
)
v1_router.include_router(
    saved_searches.router, prefix="/saved-searches", tags=["v1-saved-searches"]
)
v1_router.include_router(preferences.router, tags=["v1-preferences"])
v1_router.include_router(
    rate_limits.router, prefix="/rate-limits", tags=["v1-rate-limits"]
)
v1_router.include_router(health.router, prefix="/health", tags=["v1-health"])
v1_router.include_router(websocket.router, tags=["v1-websocket"])
v1_router.include_router(auth.router, tags=["v1-authentication"])
v1_router.include_router(phase2_monitoring.router, tags=["v1-phase2-monitoring"])
v1_router.include_router(translation_memory.router, tags=["v1-translation-memory"])
v1_router.include_router(ai_suggestions.router, tags=["v1-ai-suggestions"])
v1_router.include_router(content_generation.router, tags=["v1-content-generation"])
v1_router.include_router(templates.router, tags=["v1-templates"])
v1_router.include_router(bilingual_documents.router, tags=["v1-bilingual-documents"])
v1_router.include_router(translation_quality.router, tags=["v1-translation-quality"])
v1_router.include_router(rlhf.router, tags=["v1-rlhf"])
