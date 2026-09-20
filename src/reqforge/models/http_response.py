"""
HTTP Response model for representing an HTTP response.
"""

from typing import Dict, Any, Optional
from .base import BaseModel
from pydantic import Field


class HTTPResponse(BaseModel):
    """Represents an HTTP response."""

    type: str = Field(default="http_response", frozen=True)
    request_id: str = Field(description="ID of the request that generated this response")
    status_code: int = Field(description="HTTP status code")
    status_text: str = Field(description="HTTP status text")
    headers: Dict[str, Any] = Field(
        default_factory=dict,
        description="Response headers"
    )
    body: Optional[Any] = Field(
        default=None,
        description="Response body (can be dict, string, bytes, etc.)"
    )
    body_size: int = Field(
        default=0,
        description="Response body size in bytes"
    )
    elapsed_time: int = Field(
        default=0,
        description="Elapsed time in milliseconds"
    )
    redirect_count: int = Field(
        default=0,
        description="Number of redirects followed"
    )
    timestamp: Optional[str] = Field(
        default=None,
        description="Timestamp when the response was received (ISO format)"
    )