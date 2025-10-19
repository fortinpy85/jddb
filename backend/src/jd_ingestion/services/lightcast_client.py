"""
Lightcast API Client for Skills Extraction and Job Title Standardization.

This module provides a client for interacting with the Lightcast API,
formerly known as EMSI (Economic Modeling Specialists International).
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel

from jd_ingestion.config.settings import settings

logger = logging.getLogger(__name__)


class LightcastAuthToken(BaseModel):
    """Model for Lightcast OAuth token response."""

    access_token: str
    token_type: str
    expires_in: int
    expires_at: Optional[datetime] = None

    def __init__(self, **data):
        """Initialize token and calculate expiration time."""
        super().__init__(**data)
        if not self.expires_at:
            # Set expiration time with a 5-minute buffer
            self.expires_at = datetime.utcnow() + timedelta(
                seconds=self.expires_in - 300
            )

    def is_expired(self) -> bool:
        """Check if the token is expired."""
        if self.expires_at is None:
            return True
        return datetime.utcnow() >= self.expires_at


class ExtractedSkill(BaseModel):
    """Model for a skill extracted from text."""

    id: str
    name: str
    confidence: float
    type: Optional[str] = None

    class Config:
        """Pydantic configuration."""

        extra = "allow"


class LightcastClient:
    """
    Client for interacting with the Lightcast API.

    Handles OAuth authentication, token caching, and API requests
    for skills extraction and job title standardization.
    """

    def __init__(self):
        """Initialize the Lightcast API client."""
        self.client_id = settings.lightcast_client_id
        self.client_secret = settings.lightcast_client_secret
        self.scope = settings.lightcast_scope
        self.base_url = settings.lightcast_api_base_url
        self.timeout = settings.lightcast_request_timeout
        self.max_retries = settings.lightcast_max_retries

        self._token: Optional[LightcastAuthToken] = None
        self._http_client: Optional[httpx.AsyncClient] = None

        # API endpoints
        self.auth_url = f"{self.base_url}/connect/token"
        self.skills_api_base = "https://emsiservices.com/skills"

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
            )
        return self._http_client

    async def close(self):
        """Close the HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    async def _authenticate(self) -> LightcastAuthToken:
        """
        Authenticate with Lightcast API and obtain access token.

        Returns:
            LightcastAuthToken: The access token and metadata

        Raises:
            httpx.HTTPError: If authentication fails
        """
        logger.info("Authenticating with Lightcast API")

        client = await self._get_http_client()

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
            "scope": self.scope,
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }

        try:
            response = await client.post(
                self.auth_url,
                data=data,
                headers=headers,
            )
            response.raise_for_status()

            token_data = response.json()
            self._token = LightcastAuthToken(**token_data)

            logger.info(
                f"Successfully authenticated. Token expires in {self._token.expires_in} seconds"
            )
            return self._token

        except httpx.HTTPError as e:
            logger.error(f"Failed to authenticate with Lightcast API: {e}")
            raise

    async def _get_valid_token(self) -> str:
        """
        Get a valid access token, refreshing if necessary.

        Returns:
            str: Valid access token
        """
        if self._token is None or self._token.is_expired():
            await self._authenticate()

        assert self._token is not None, "Authentication failed to set token"
        return self._token.access_token

    async def _make_request(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Make an authenticated request to the Lightcast API.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL to request
            **kwargs: Additional arguments to pass to httpx

        Returns:
            Dict: JSON response from the API

        Raises:
            httpx.HTTPError: If the request fails
        """
        token = await self._get_valid_token()
        client = await self._get_http_client()

        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token}"

        retries = 0
        last_exception: Optional[Exception] = None  # type: ignore[syntax]

        while retries <= self.max_retries:
            try:
                response = await client.request(
                    method,
                    url,
                    headers=headers,
                    **kwargs,
                )
                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    # Token might be invalid, force re-authentication
                    logger.warning("Received 401, re-authenticating")
                    self._token = None
                    token = await self._get_valid_token()
                    headers["Authorization"] = f"Bearer {token}"
                    retries += 1
                    last_exception = e
                    continue
                else:
                    logger.error(f"HTTP error: {e}")
                    raise

            except httpx.HTTPError as e:
                retries += 1
                last_exception = e
                if retries <= self.max_retries:
                    logger.warning(
                        f"Request failed (attempt {retries}/{self.max_retries}): {e}"
                    )
                    continue
                else:
                    break

        logger.error(f"Max retries exceeded. Last error: {last_exception}")
        if last_exception is not None:
            raise last_exception
        raise httpx.HTTPError("Request failed with no recorded exception")

    async def extract_skills(
        self,
        text: str,
        version: str = "latest",
        confidence_threshold: float = 0.5,
    ) -> List[ExtractedSkill]:
        """
        Extract skills from text using the Lightcast Skills API.

        Args:
            text: The text to extract skills from
            version: API version to use (default: "latest")
            confidence_threshold: Minimum confidence score (0.0-1.0)

        Returns:
            List[ExtractedSkill]: List of extracted skills

        Raises:
            httpx.HTTPError: If the API request fails
        """
        logger.info(f"Extracting skills from text (length: {len(text)} chars)")

        url = f"{self.skills_api_base}/versions/{version}/extract"

        payload = {
            "text": text,
            "confidenceThreshold": confidence_threshold,
        }

        try:
            response_data = await self._make_request(
                "POST",
                url,
                json=payload,
            )

            skills = []
            for skill_data in response_data.get("data", []):
                skill = ExtractedSkill(
                    id=skill_data.get("skill", {}).get("id", ""),
                    name=skill_data.get("skill", {}).get("name", ""),
                    confidence=skill_data.get("confidence", 0.0),
                    type=skill_data.get("skill", {}).get("type"),
                )
                skills.append(skill)

            logger.info(f"Extracted {len(skills)} skills")
            return skills

        except httpx.HTTPError as e:
            logger.error(f"Failed to extract skills: {e}")
            raise

    async def extract_skills_with_trace(
        self,
        text: str,
        version: str = "latest",
        confidence_threshold: float = 0.5,
    ) -> Dict[str, Any]:
        """
        Extract skills with trace information showing where skills were found.

        Args:
            text: The text to extract skills from
            version: API version to use (default: "latest")
            confidence_threshold: Minimum confidence score (0.0-1.0)

        Returns:
            Dict: Skills with trace information

        Raises:
            httpx.HTTPError: If the API request fails
        """
        logger.info(
            f"Extracting skills with trace from text (length: {len(text)} chars)"
        )

        url = f"{self.skills_api_base}/versions/{version}/extract/trace"

        payload = {
            "text": text,
            "confidenceThreshold": confidence_threshold,
        }

        try:
            response_data = await self._make_request(
                "POST",
                url,
                json=payload,
            )

            logger.info("Extracted skills with trace information")
            return response_data

        except httpx.HTTPError as e:
            logger.error(f"Failed to extract skills with trace: {e}")
            raise

    async def get_skill_info(
        self,
        skill_id: str,
        version: str = "latest",
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific skill.

        Args:
            skill_id: The Lightcast skill ID
            version: API version to use (default: "latest")

        Returns:
            Dict: Skill information

        Raises:
            httpx.HTTPError: If the API request fails
        """
        logger.info(f"Getting info for skill: {skill_id}")

        url = f"{self.skills_api_base}/versions/{version}/skills/{skill_id}"

        try:
            response_data = await self._make_request("GET", url)
            return response_data

        except httpx.HTTPError as e:
            logger.error(f"Failed to get skill info: {e}")
            raise

    async def standardize_title(
        self,
        job_description_text: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Get standardized job title suggestions based on job description text.

        Note: This is a placeholder. The actual endpoint may differ based on
        your Lightcast subscription and available APIs.

        Args:
            job_description_text: The job description text
            limit: Maximum number of suggestions to return

        Returns:
            List[Dict]: List of standardized title suggestions

        Raises:
            NotImplementedError: Job title standardization endpoint not yet configured
        """
        # TODO: Implement based on available Lightcast Job Titles API
        # This will depend on the specific Lightcast API subscription
        logger.warning(
            "Job title standardization not yet implemented. "
            "Requires Lightcast Job Titles API access."
        )
        raise NotImplementedError(
            "Job title standardization endpoint not configured. "
            "Please verify Lightcast API subscription includes Job Titles API."
        )


# Singleton instance
_lightcast_client: Optional[LightcastClient] = None


async def get_lightcast_client() -> LightcastClient:
    """
    Get the singleton Lightcast client instance.

    Returns:
        LightcastClient: The Lightcast API client
    """
    global _lightcast_client
    if _lightcast_client is None:
        _lightcast_client = LightcastClient()
    return _lightcast_client


async def close_lightcast_client():
    """Close the Lightcast client and cleanup resources."""
    global _lightcast_client
    if _lightcast_client:
        await _lightcast_client.close()
        _lightcast_client = None
