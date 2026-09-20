"""
HTTP client for ReqForge.
"""

import httpx
from typing import Optional, Dict, Any
from ..config import get_config
from ..core.logging import get_logger


logger = get_logger(__name__)


class HTTPClient:
    """Async HTTP client for making requests."""

    def __init__(self):
        """Initialize the HTTP client."""
        self.config = get_config()
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client instance."""
        if self._client is None:
            # Configure HTTPX client
            limits = httpx.Limits(
                max_connections=self.config.http.concurrency,
                max_keepalive_connections=self.config.http.concurrency
            )

            # Configure proxies if set
            # Proxies support will be added in a later phase
            proxies = None

            self._client = httpx.AsyncClient(
                timeout=self.config.http.timeout,
                limits=limits,
                follow_redirects=self.config.http.follow_redirects,
                verify=self.config.http.verify_ssl,
                headers={"User-Agent": self.config.http.user_agent}
            )
        return self._client

    async def request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
        data: Any = None,
        json: Any = None,
        timeout: Optional[float] = None
    ) -> httpx.Response:
        """
        Make an HTTP request.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            params: Query parameters
            headers: Request headers
            data: Request body data
            json: JSON body data
            timeout: Request timeout in seconds

        Returns:
            HTTPX Response object
        """
        client = await self._get_client()
        logger.debug(f"Making {method} request to {url}")

        response = await client.request(
            method=method,
            url=url,
            params=params,
            headers=headers,
            data=data,
            json=json,
            timeout=timeout or self.config.http.timeout
        )

        logger.debug(f"Received response: {response.status_code}")
        return response

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None