"""
HTTP Request model for representing an HTTP request.
"""

from typing import Dict, Any, Optional
from .base import BaseModel
from pydantic import Field


class HTTPRequest(BaseModel):
    """Represents an HTTP request."""

    type: str = Field(default="http_request", frozen=True)
    method: str = Field(description="HTTP method (GET, POST, etc.)")
    url: str = Field(description="Request URL")
    headers: Dict[str, Any] = Field(
        default_factory=dict,
        description="Request headers"
    )
    body: Optional[Any] = Field(
        default=None,
        description="Request body (can be dict, string, bytes, etc.)"
    )
    http_version: str = Field(
        default="HTTP/1.1",
        description="HTTP version"
    )