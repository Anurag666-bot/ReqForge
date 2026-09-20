"""
Finding model for representing a security finding.
"""

from typing import List, Dict, Any, Optional
from .base import BaseModel
from pydantic import Field
from enum import Enum


class SeverityLevel(str, Enum):
    """Finding severity levels."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class FindingCategory(str, Enum):
    """Categories of findings."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    INPUT_VALIDATION = "input-validation"
    BUSINESS_LOGIC = "business-logic"
    CONFIGURATION = "configuration"
    INFORMATION_DISCLOSURE = "information-disclosure"
    SESSION_MANAGEMENT = "session-management"
    CRYPTOGRAPHY = "cryptography"
    DIRECTORY_TRAVERSAL = "directory-traversal"
    FILE_UPLOAD = "file-upload"
    XXE = "xxe"
    SSRF = "ssrf"
    OPEN_REDIRECT = "open-redirect"
    CORS = "cors"
    CSP = "csp"
    RATE_LIMITING = "rate-limiting"
    OTHER = "other"


class Finding(BaseModel):
    """Represents a security finding."""

    type: str = Field(default="finding", frozen=True)
    title: str = Field(description="Finding title")
    description: str = Field(description="Finding description")
    severity: str = Field(
        default=SeverityLevel.INFO.value,
        description="Finding severity"
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence in the finding (0.0 to 1.0)"
    )
    asset: Optional[str] = Field(
        default=None,
        description="ID of the asset related to this finding"
    )
    endpoint: Optional[str] = Field(
        default=None,
        description="ID of the endpoint related to this finding"
    )
    category: str = Field(
        default=FindingCategory.OTHER.value,
        description="Finding category"
    )
    evidence: List[str] = Field(
        default_factory=list,
        description="List of related request/response IDs"
    )
    impact: Optional[str] = Field(
        default=None,
        description="Description of the potential impact"
    )
    remediation: Optional[str] = Field(
        default=None,
        description="Recommended remediation steps"
    )
    references: List[str] = Field(
        default_factory=list,
        description="Reference links (e.g., OWASP, CVE)"
    )
    state: str = Field(
        default="OBSERVED",
        description="Finding state: OBSERVED, INTERESTING, NEEDS_REVIEW, CONFIRMED, FALSE_POSITIVE"
    )