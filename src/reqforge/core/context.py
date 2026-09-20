"""
Context for ReqForge scanning/testing sessions.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from ..scope.validator import Scope, get_scope
from ..core.logging import get_logger


logger = get_logger(__name__)


class ScanContext:
    """Context for a testing/scan session."""

    def __init__(self, target: str):
        """
        Initialize scan context.

        Args:
            target: Target to test (domain, subdomain, or URL)
        """
        self.target = target
        self.scope = get_scope()  # Use global scope
        self.start_time = datetime.utcnow()
        self.end_time: Optional[datetime] = None
        self.status = "initialized"  # initialized, running, completed, failed, cancelled
        self.history: List[Dict[str, Any]] = []  # List of executed requests
        self.evidence: List[Dict[str, Any]] = []  # List of evidence records
        self.findings: List[Dict[str, Any]] = []  # List of findings
        self.scan_id: Optional[str] = None  # Will be set when saved to storage
        self.modules_enabled: Dict[str, bool] = {}  # Track which modules are enabled
        self.errors: List[str] = []  # List of error messages
        self.metadata: Dict[str, Any] = {}  # Additional metadata

    def set_status(self, status: str) -> None:
        """
        Set the context status.

        Args:
            status: New status value
        """
        self.status = status
        logger.debug(f"Scan context status set to: {status}")

    def add_to_history(self, entry: Dict[str, Any]) -> None:
        """
        Add an entry to the history.

        Args:
            entry: History entry to add
        """
        self.history.append(entry)
        logger.debug(f"Added entry to history: {entry.get('id', 'unknown')}")

    def add_evidence(self, evidence: Dict[str, Any]) -> None:
        """
        Add an evidence record.

        Args:
            evidence: Evidence record to add
        """
        self.evidence.append(evidence)
        logger.debug(f"Added evidence: {evidence.get('id', 'unknown')}")

    def add_finding(self, finding: Dict[str, Any]) -> None:
        """
        Add a finding.

        Args:
            finding: Finding to add
        """
        self.findings.append(finding)
        logger.debug(f"Added finding: {finding.get('id', 'unknown')}")

    def add_error(self, error: str) -> None:
        """
        Add an error message.

        Args:
            error: Error message to add
        """
        self.errors.append(error)
        logger.error(f"Added error: {error}")

    def is_scope_allowed(self, target: str) -> bool:
        """
        Check if a target is within scope.

        Args:
            target: URL or hostname to check

        Returns:
            True if target is allowed, False otherwise
        """
        return self.scope.is_allowed(target)

    def validate_scope(self, target: str) -> None:
        """
        Validate that a target is within scope.

        Args:
            target: URL or hostname to validate

        Raises:
            ScopeValidationError: If target is not within scope
        """
        self.scope.validate(target)

    def get_duration(self) -> Optional[float]:
        """
        Get the duration of the scan in seconds.

        Returns:
            Duration in seconds, or None if not completed
        """
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert context to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "target": self.target,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status,
            "history_count": len(self.history),
            "evidence_count": len(self.evidence),
            "findings_count": len(self.findings),
            "scan_id": self.scan_id,
            "modules_enabled": self.modules_enabled,
            "errors": self.errors,
            "metadata": self.metadata
        }