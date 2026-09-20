"""
SQLAlchemy models for ReqForge storage.
"""

import json
from datetime import datetime
from typing import Any, List, Optional
from sqlalchemy import Column, String, DateTime, Integer, Boolean, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class History(Base):
    """Stores executed requests and their responses."""

    __tablename__ = "history"

    id = Column(String, primary_key=True, index=True)
    # Store the request as JSON
    request = Column(JSON, nullable=False)
    # Store the response as JSON (nullable for failed requests)
    response = Column(JSON, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    status_code = Column(Integer, nullable=True)
    elapsed_time = Column(Integer, nullable=True)  # in milliseconds
    # Optional: store the target/scope for quick filtering
    target = Column(String, nullable=True, index=True)


class Evidence(Base):
    """Stores evidence records."""

    __tablename__ = "evidence"

    id = Column(String, primary_key=True, index=True)
    request_id = Column(String, nullable=False, index=True)
    response_id = Column(String, nullable=True, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    mutation = Column(Text, nullable=True)
    comparison = Column(JSON, nullable=True)  # Store comparison data as JSON
    notes = Column(Text, nullable=True)
    screenshots = Column(JSON, nullable=True)  # List of screenshot paths


class Finding(Base):
    """Stores findings."""

    __tablename__ = "findings"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String, nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    confidence = Column(Integer, nullable=False)  # Store as integer percentage (0-100) or float? Let's use integer 0-100 for simplicity.
    asset_id = Column(String, nullable=True, index=True)
    endpoint_id = Column(String, nullable=True, index=True)
    category = Column(String, nullable=False)
    # Store evidence IDs as JSON list
    evidence_ids = Column(JSON, nullable=False, default=list)
    impact = Column(Text, nullable=True)
    remediation = Column(Text, nullable=True)
    references = Column(JSON, nullable=True, default=list)  # List of reference URLs
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    state = Column(String, nullable=False)  # OBSERVED, INTERESTING, NEEDS_REVIEW, CONFIRMED, FALSE_POSITIVE


class Endpoint(Base):
    """Stores discovered endpoints."""

    __tablename__ = "endpoints"

    id = Column(String, primary_key=True, index=True)
    url = Column(String, nullable=False, index=True)
    domain = Column(String, nullable=False, index=True)  # Extract domain from URL for filtering
    method = Column(String, nullable=True, default="GET")
    endpoint_type = Column(String, nullable=True, default="unknown")  # page, api, asset, document, etc.
    source = Column(String, nullable=True, default="imported")  # How was it discovered
    status_code = Column(Integer, nullable=True)  # HTTP status code if probed
    content_type = Column(String, nullable=True)
    parameters = Column(JSON, nullable=True, default=dict)  # Parameters associated with the endpoint
    headers = Column(JSON, nullable=True, default=dict)  # Headers associated with the endpoint
    tags = Column(JSON, nullable=True, default=list)  # Tags for categorization
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)


class Scan(Base):
    """Stores scan/run information."""

    __tablename__ = "scans"

    id = Column(String, primary_key=True, index=True)
    start_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)  # in seconds
    requests_sent = Column(Integer, nullable=False, default=0)
    findings_generated = Column(Integer, nullable=False, default=0)
    profile_used = Column(String, nullable=True)
    # Store target IDs as JSON list
    targets = Column(JSON, nullable=False, default=list)