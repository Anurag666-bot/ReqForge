"""
Scan model for representing a testing session or run.
"""

from typing import List, Dict, Any, Optional
from .base import BaseModel
from pydantic import Field


class Scan(BaseModel):
    """Represents a testing session or run."""

    type: str = Field(default="scan", frozen=True)
    start_time: str = Field(
        description="Start time of the scan (ISO format)"
    )
    end_time: Optional[str] = Field(
        default=None,
        description="End time of the scan (ISO format)"
    )
    duration_seconds: Optional[float] = Field(
        default=None,
        description="Duration of the scan in seconds"
    )
    requests_sent: int = Field(
        default=0,
        description="Number of requests sent during the scan"
    )
    findings_generated: int = Field(
        default=0,
        description="Number of findings generated during the scan"
    )
    profile_used: Optional[str] = Field(
        default=None,
        description="Name of the testing profile used"
    )
    targets: List[str] = Field(
        default_factory=list,
        description="List of target IDs involved in the scan"
    )