"""Scope validation engine for ReqForge."""

from __future__ import annotations

from urllib.parse import urlparse


class ScopeValidationError(ValueError):
    """Raised when a target is outside the allowed scope."""


class Scope:
    """Simple domain-based scope checker for ReqForge."""

    def __init__(self, allowed_domains=None, blocked_domains=None, allow_subdomains=True):
        self.allowed_domains = [self._normalize_domain(d) for d in (allowed_domains or []) if d]
        self.blocked_domains = [self._normalize_domain(d) for d in (blocked_domains or []) if d]
        self.allow_subdomains = allow_subdomains

    @staticmethod
    def _normalize_domain(domain: str) -> str:
        value = (domain or "").strip().lower().strip(".")
        if not value:
            return ""
        if "//" not in value and "://" not in value:
            value = f"https://{value}"
        parsed = urlparse(value)
        host = parsed.hostname or value.split("//", 1)[-1].split("/", 1)[0]
        return host.strip(".").lower()

    @staticmethod
    def _hostname_from_target(target: str) -> str:
        value = (target or "").strip()
        if not value:
            return ""
        if "//" not in value:
            value = f"https://{value}"
        parsed = urlparse(value)
        hostname = parsed.hostname or value.split("//", 1)[-1].split("/", 1)[0]
        return hostname.strip(".").lower()

    def _matches(self, hostname: str, domain: str) -> bool:
        if not domain:
            return False
        if hostname == domain:
            return True
        if self.allow_subdomains and hostname.endswith(f".{domain}"):
            return True
        return False

    def is_allowed(self, target: str) -> bool:
        """Check if the given target is within scope."""
        hostname = self._hostname_from_target(target)
        if not hostname:
            return False

        for blocked in self.blocked_domains:
            if blocked and self._matches(hostname, blocked):
                return False

        if not self.allowed_domains:
            return True

        for allowed in self.allowed_domains:
            if self._matches(hostname, allowed):
                return True
        return False

    def validate(self, target: str) -> None:
        """Validate a target against the current scope."""
        if not self.is_allowed(target):
            raise ScopeValidationError(f"Target '{target}' is outside the configured scope.")

    def add_allowed(self, domain: str) -> None:
        """Add a domain to the allowed scope."""
        normalized = self._normalize_domain(domain)
        if normalized and normalized not in self.allowed_domains:
            self.allowed_domains.append(normalized)

    def add_blocked(self, domain: str) -> None:
        """Add a domain to the blocked scope."""
        normalized = self._normalize_domain(domain)
        if normalized and normalized not in self.blocked_domains:
            self.blocked_domains.append(normalized)


_GLOBAL_SCOPE = Scope()


def get_scope() -> Scope:
    """Return the current global scope instance."""
    return _GLOBAL_SCOPE


def set_scope(scope: Scope) -> Scope:
    """Override the global scope instance."""
    global _GLOBAL_SCOPE
    _GLOBAL_SCOPE = scope
    return _GLOBAL_SCOPE


def is_in_scope(target: str) -> bool:
    """Check whether a target matches the global scope."""
    return get_scope().is_allowed(target)


def validate_scope(target: str) -> None:
    """Validate a target against the global scope."""
    get_scope().validate(target)


ScopeInstance = Scope
ScopeClass = Scope

# Backward-compatible aliases
Scope = Scope