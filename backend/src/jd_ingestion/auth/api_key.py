# Standard library imports
from typing import Optional

# Third-party imports
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

# Local imports
from ..config.settings import settings
from ..utils.logging import get_logger

# auto_error=False allows the header to be optional - FastAPI won't auto-reject missing headers
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
logger = get_logger(__name__)


def get_api_key(api_key_header: Optional[str] = Security(API_KEY_HEADER)) -> str:
    """Check for API key in request header.

    In development mode, authentication is bypassed.
    In production mode, requires valid X-API-Key header.
    """
    logger.info(
        f"get_api_key called. is_development: {settings.is_development}, api_key_header_present: {api_key_header is not None}"
    )

    # In development, bypass authentication
    if settings.is_development:
        logger.info("Development mode: bypassing authentication")
        return "development_key"

    # In production, require valid API key
    if api_key_header is None:
        logger.warning("Production mode: API key header missing")
        raise HTTPException(
            status_code=403,
            detail="Not authenticated",
        )

    if api_key_header == settings.API_KEY:
        return api_key_header
    else:
        logger.warning("Production mode: Invalid API key provided")
        raise HTTPException(
            status_code=403,
            detail="Could not validate credentials",
        )
