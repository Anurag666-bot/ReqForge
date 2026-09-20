"""
Scope model for representing scope constraints.
"""

from typing import List, Optional
from .base import BaseModel
from pydantic import Field


class Scope(BaseModel):
    """Represents a scope definition with allowed and blocked domains."""

    type: str = Field(default="scope", frozen=True)
    allowed_domains: List[str] = Field(
        default_factory=list,
        description="List of allowed domains (supports wildcards)"
    )
    blocked_domains: List[str] = Field(
        default_factory=list,
        description="List of blocked domains (supports wildcards)"
    )
    allow_subdomains: bool = Field(
        default=True,
        description="Whether to allow subdomains of allowed domains"
    )