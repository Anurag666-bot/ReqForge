"""
Endpoint model for representing a discovered endpoint.
"""

from typing import Dict, Any, Optional
from .base import BaseModel
from pydantic import Field
from enum import Enum


class EndpointType(str, Enum):
    """Types of endpoints."""
    PAGE = "page"
    API = "api"
    ASSET = "asset"
    DOCUMENT = "document"
    AUTHENTICATION = "authentication"
    UNKNOWN = "unknown"


class Endpoint(BaseModel):
    """Represents a discovered endpoint."""

    type: str = Field(default="endpoint", frozen=True)
    url: str = Field(description="Endpoint URL")
    endpoint_type: str = Field(
        default=EndpointType.UNKNOWN.value,
        description="Type of endpoint"
    )
    source: str = Field(
        default="unknown",
        description="How this endpoint was discovered"
    )
    method: Optional[str] = Field(
        default=None,
        description="HTTP method if known"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters associated with the endpoint"
    )
    headers: Dict[str, Any] = Field(
        default_factory=dict,
        description="Headers associated with the endpoint"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Tags for categorization"
    )