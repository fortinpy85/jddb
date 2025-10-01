# Standard library imports

# Third-party imports
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

# Local imports
from ..config.settings import settings

API_KEY_HEADER = APIKeyHeader(name="X-API-Key")


def get_api_key(api_key_header: str = Security(API_KEY_HEADER)) -> str:
    """Check for API key in request header."""
    if api_key_header == settings.API_KEY:
        return api_key_header
    else:
        raise HTTPException(
            status_code=403,
            detail="Could not validate credentials",
        )
