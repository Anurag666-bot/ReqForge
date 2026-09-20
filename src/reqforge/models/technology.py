"""
Technology model for representing a detected technology.
"""

from typing import List, Dict, Any, Optional
from .base import BaseModel
from pydantic import Field
from enum import Enum


class TechnologyCategory(str, Enum):
    """Categories of technology."""
    WEB_SERVER = "web_server"
    FRAMEWORK = "framework"
    CMS = "cms"
    LANGUAGE = "language"
    DATABASE = "database"
    CDN = "cdn"
    SECURITY = "security"
    PROGRAMMING_LANGUAGE = "programming_language"
    JAVASCRIPT_FRAMEWORK = "javascript_framework"
    WEB_FRAMEWORK = "web_framework"
    OTHER = "other"


class Technology(BaseModel):
    """Represents a detected technology."""

    type: str = Field(default="technology", frozen=True)
    name: str = Field(description="Technology name")
    category: str = Field(
        default=TechnologyCategory.OTHER.value,
        description="Technology category"
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Detection confidence (0.0 to 1.0)"
    )
    evidence: List[str] = Field(
        default_factory=list,
        description="Evidence for the detection"
    )
    hostname: str = Field(
        description="Hostname where the technology was detected"
    )
    version: Optional[str] = Field(
        default=None,
        description="Detected version if available"
    )