"""
Evidence model for representing a piece of evidence.
"""

from typing import List, Dict, Any, Optional
from .base import BaseModel
from pydantic import Field


class Evidence(BaseModel):
    """Represents a piece of evidence (request/response pair with context)."""

    type: str = Field(default="evidence", frozen=True)
    request_id: str = Field(description="ID of the request")
    response_id: Optional[str] = Field(
        default=None,
        description="ID of the response (if available)"
    )
    timestamp: str = Field(
        description="Timestamp when the evidence was captured"
    )
    mutation: Optional[str] = Field(
        default=None,
        description="Description of the mutation applied (if any)"
    )
    comparison: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Comparison data with baseline (if applicable)"
    )
    notes: Optional[str] = Field(
        default=None,
        description="Analyst notes"
    )
    screenshots: List[str] = Field(
        default_factory=list,
        description="Paths to screenshot files (if any)"
    )