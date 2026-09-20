"""
Target model for representing a security testing target.
"""

from .base import BaseModel
from pydantic import Field


class Target(BaseModel):
    """Represents a target for security testing."""

    type: str = Field(default="target", frozen=True)
    value: str = Field(
        description="Target value (domain, IP, URL, etc.)"
    )