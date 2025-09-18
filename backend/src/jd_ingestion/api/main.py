# Standard library imports
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

# Third-party imports
import uvicorn
from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

# Local imports
from ..config import settings
from ..database.connection import configure_mappers, get_async_session
from ..middleware.analytics_middleware import AnalyticsMiddleware
from ..utils.logging import configure_logging, get_logger
from .endpoints import (
    analysis,
    analytics,
    health,
    ingestion,
    jobs,
    performance,
    quality,
    rate_limits,
    saved_searches,
    search,
    search_analytics,
    tasks,
)

# Configure logging
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    logger.info(
        "Starting JDDB - Government Job Description Database API",
        version="1.0.0",
        debug=settings.debug,
    )

    # Ensure SQLAlchemy mappers are configured
    configure_mappers()
    logger.info("Database mappers configured successfully")

    yield

    # Shutdown
    logger.info("Shutting down JDDB - Government Job Description Database API")


# Create FastAPI app
app = FastAPI(
    title="JDDB - Government Job Description Database",
    description="""
    ## Government Job Description Management System

    A comprehensive API for processing, managing, and searching government job description files.
    Built for the Government of Canada to modernize job description workflows.

    ### Key Features
    - **File Processing**: Support for .txt, .doc, .docx, and .pdf formats
    - **Semantic Search**: AI-powered search with pgvector and OpenAI embeddings
    - **Bilingual Support**: Full English/French language support
    - **Content Analysis**: Automated parsing of job sections and metadata
    - **Quality Assurance**: Built-in validation and quality checks
    - **Analytics**: Comprehensive usage tracking and analytics

    ### API Documentation
    - **Interactive Docs**: Available at `/api/docs`
    - **OpenAPI Schema**: Available at `/api/openapi.json`
    - **Health Check**: Available at `/health`

    ### Authentication
    Currently operating in development mode. Production deployment will include
    appropriate government authentication mechanisms.

    ### Support
    For issues and support, visit: https://github.com/fortinpy85/jddb/issues
    """,
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
    contact={
        "name": "JDDB Development Team",
        "url": "https://github.com/fortinpy85/jddb",
        "email": "support@jddb.gov.ca",
    },
    license_info={
        "name": "MIT License",
        "url": "https://github.com/fortinpy85/jddb/blob/main/LICENSE",
    },
    servers=[
        {"url": "http://localhost:8000", "description": "Development server"},
        {
            "url": "https://api.jddb.gov.ca",
            "description": "Production server (placeholder)",
        },
    ],
)

# Add CORS middleware with production-ready configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Add analytics middleware
app.add_middleware(AnalyticsMiddleware, track_all_requests=True)

# Include API routers
app.include_router(ingestion.router, prefix="/api/ingestion", tags=["ingestion"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
app.include_router(quality.router, prefix="/api/quality", tags=["quality"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(performance.router, prefix="/api/performance", tags=["performance"])
app.include_router(
    saved_searches.router, prefix="/api/saved-searches", tags=["saved-searches"]
)
app.include_router(
    search_analytics.router, prefix="/api/search-analytics", tags=["search-analytics"]
)
app.include_router(rate_limits.router, prefix="/api/rate-limits", tags=["rate-limits"])
app.include_router(health.router, prefix="/api/health", tags=["health"])


@app.get("/")
async def root():
    """Root endpoint with basic API information."""
    return {
        "name": "JDDB - Government Job Description Database",
        "version": "1.0.0",
        "description": "Government of Canada Job Description Management System",
        "docs_url": "/api/docs",
        "openapi_url": "/api/openapi.json",
        "health_url": "/health",
        "repository": "https://github.com/fortinpy85/jddb",
        "features": [
            "File Processing (.txt, .doc, .docx, .pdf)",
            "Semantic Search with AI",
            "Bilingual Support (EN/FR)",
            "Content Analysis & Parsing",
            "Quality Assurance",
            "Analytics & Monitoring",
        ],
    }


@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_async_session)):
    """Health check endpoint."""
    try:
        # Test database connection
        await db.execute("SELECT 1")

        return {"status": "healthy", "database": "connected", "version": "1.0.0"}
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service unavailable")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(
        "Unhandled exception",
        request_url=str(request.url),
        error=str(exc),
        exc_info=True,
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
        },
    )


def create_app() -> FastAPI:
    """Factory function to create the FastAPI app."""
    return app


if __name__ == "__main__":
    uvicorn.run(
        "jd_ingestion.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
