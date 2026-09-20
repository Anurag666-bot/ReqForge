"""
Data access layer for ReqForge storage.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from . import models


class HistoryRepository:
    """Repository for history records."""

    def __init__(self, session: Session):
        self.session = session

    def add(self, history: models.History) -> models.History:
        """Add a history record."""
        self.session.add(history)
        self.session.commit()
        self.session.refresh(history)
        return history

    def get(self, id: str) -> Optional[models.History]:
        """Get a history record by ID."""
        return self.session.query(models.History).filter(models.History.id == id).first()

    def list(self, limit: int = 50, offset: int = 0) -> List[models.History]:
        """List history records."""
        return self.session.query(models.History).order_by(models.History.timestamp.desc()).offset(offset).limit(limit).all()

    def delete(self, id: str) -> bool:
        """Delete a history record by ID."""
        history = self.get(id)
        if history:
            self.session.delete(history)
            self.session.commit()
            return True
        return False


class EvidenceRepository:
    """Repository for evidence records."""

    def __init__(self, session: Session):
        self.session = session

    def add(self, evidence: models.Evidence) -> models.Evidence:
        """Add an evidence record."""
        self.session.add(evidence)
        self.session.commit()
        self.session.refresh(evidence)
        return evidence

    def get(self, id: str) -> Optional[models.Evidence]:
        """Get an evidence record by ID."""
        return self.session.query(models.Evidence).filter(models.Evidence.id == id).first()

    def list(self, limit: int = 50, offset: int = 0) -> List[models.Evidence]:
        """List evidence records."""
        return self.session.query(models.Evidence).order_by(models.Evidence.timestamp.desc()).offset(offset).limit(limit).all()

    def delete(self, id: str) -> bool:
        """Delete an evidence record by ID."""
        evidence = self.get(id)
        if evidence:
            self.session.delete(evidence)
            self.session.commit()
            return True
        return False


class FindingRepository:
    """Repository for findings."""

    def __init__(self, session: Session):
        self.session = session

    def add(self, finding: models.Finding) -> models.Finding:
        """Add a finding."""
        self.session.add(finding)
        self.session.commit()
        self.session.refresh(finding)
        return finding

    def get(self, id: str) -> Optional[models.Finding]:
        """Get a finding by ID."""
        return self.session.query(models.Finding).filter(models.Finding.id == id).first()

    def list(self, limit: int = 50, offset: int = 0) -> List[models.Finding]:
        """List findings."""
        return self.session.query(models.Finding).order_by(models.Finding.timestamp.desc()).offset(offset).limit(limit).all()

    def delete(self, id: str) -> bool:
        """Delete a finding by ID."""
        finding = self.get(id)
        if finding:
            self.session.delete(finding)
            self.session.commit()
            return True
        return False


class ScanRepository:
    """Repository for scan records."""

    def __init__(self, session: Session):
        self.session = session

    def add(self, scan: models.Scan) -> models.Scan:
        """Add a scan."""
        self.session.add(scan)
        self.session.commit()
        self.session.refresh(scan)
        return scan

    def get(self, id: str) -> Optional[models.Scan]:
        """Get a scan by ID."""
        return self.session.query(models.Scan).filter(models.Scan.id == id).first()

    def list(self, limit: int = 50, offset: int = 0) -> List[models.Scan]:
        """List scans."""
        return self.session.query(models.Scan).order_by(models.Scan.start_time.desc()).offset(offset).limit(limit).all()

    def delete(self, id: str) -> bool:
        """Delete a scan by ID."""
        scan = self.get(id)
        if scan:
            self.session.delete(scan)
            self.session.commit()
            return True
        return False


class EndpointRepository:
    """Repository for endpoint records."""

    def __init__(self, session: Session):
        self.session = session

    def add(self, endpoint: models.Endpoint) -> models.Endpoint:
        """Add an endpoint."""
        self.session.add(endpoint)
        self.session.commit()
        self.session.refresh(endpoint)
        return endpoint

    def get(self, id: str) -> Optional[models.Endpoint]:
        """Get an endpoint by ID."""
        return self.session.query(models.Endpoint).filter(models.Endpoint.id == id).first()

    def list_by_domain(self, domain: str, limit: int = 50, offset: int = 0) -> List[models.Endpoint]:
        """List endpoints for a specific domain, including subdomains."""
        normalized_domain = (domain or "").strip().lower().rstrip(".")
        rows = self.session.query(models.Endpoint).order_by(models.Endpoint.url).all()
        matches = [
            row for row in rows
            if row.domain == normalized_domain or row.domain.endswith(f".{normalized_domain}")
        ]
        return matches[offset:offset + limit]

    def list_all(self, limit: int = 50, offset: int = 0) -> List[models.Endpoint]:
        """List all endpoints."""
        return self.session.query(models.Endpoint).order_by(models.Endpoint.timestamp.desc()).offset(offset).limit(limit).all()

    def delete(self, id: str) -> bool:
        """Delete an endpoint by ID."""
        endpoint = self.get(id)
        if endpoint:
            self.session.delete(endpoint)
            self.session.commit()
            return True
        return False

    def delete_by_domain(self, domain: str) -> int:
        """Delete all endpoints for a domain. Returns count of deleted records."""
        count = self.session.query(models.Endpoint).filter(models.Endpoint.domain == domain).delete()
        self.session.commit()
        return count