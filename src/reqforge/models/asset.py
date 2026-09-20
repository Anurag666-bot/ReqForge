"""
Asset model for representing a discovered asset.
"""

from typing import List, Optional, Dict, Any
from .base import BaseModel
from pydantic import Field


class Asset(BaseModel):
    """Represents a discovered asset (domain, subdomain, IP, etc.)."""

    type: str = Field(default="asset", frozen=True)
    hostname: str = Field(description="Hostname of the asset")
    ip_addresses: List[str] = Field(
        default_factory=list,
        description="List of IP addresses associated with the asset"
    )
    url: Optional[str] = Field(
        default=None,
        description="URL if applicable (e.g., for web assets)"
    )
    is_active: bool = Field(
        default=True,
        description="Whether the asset is currently active"
    )
    scope_validated: bool = Field(
        default=False,
        description="Whether this asset has been validated against scope"
    )