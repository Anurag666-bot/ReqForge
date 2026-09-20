"""
Differential response analysis engine for ReqForge.
Compares HTTP responses to identify differences.
"""

import json
import difflib
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class DiffCategory(Enum):
    """Categories of differences that can be detected."""
    STATUS_CODE = "status_code"
    HEADERS = "headers"
    BODY_SIZE = "body_size"
    BODY_CONTENT = "body_content"
    JSON_STRUCTURE = "json_structure"
    JSON_VALUES = "json_values"
    RESPONSE_TIME = "response_time"


@dataclass
class DiffResult:
    """Result of comparing two HTTP responses."""
    # Basic comparison
    status_code_changed: bool
    status_code_baseline: Optional[int]
    status_code_mutated: Optional[int]

    # Headers comparison
    headers_changed: bool
    headers_added: List[str]
    headers_removed: List[str]
    headers_changed_values: List[Tuple[str, Any, Any]]  # (header_name, baseline_value, mutated_value)

    # Body size comparison
    body_size_changed: bool
    body_size_baseline: int
    body_size_mutated: int
    body_size_delta: int  # mutated - baseline

    # Body content comparison
    body_content_changed: bool
    body_similarity: float  # 0.0 to 1.0, where 1.0 is identical

    # JSON comparison (if both responses are JSON)
    json_compared: bool
    json_structure_changed: bool
    json_values_changed: bool
    json_keys_added: List[str]
    json_keys_removed: List[str]
    json_values_changed_details: List[Tuple[str, Any, Any]]  # (key_path, baseline_value, mutated_value)

    # Response time comparison
    response_time_changed: bool
    response_time_baseline: float
    response_time_mutated: float
    response_time_delta: float  # mutated - baseline

    # Overall assessment
    has_significant_difference: bool
    change_summary: str


class DiffEngine:
    """Engine for comparing HTTP responses to identify differences."""

    @staticmethod
    def compare_responses(
        baseline_response: Dict[str, Any],
        mutated_response: Dict[str, Any]
    ) -> DiffResult:
        """
        Compare two HTTP responses and return a detailed diff.

        Args:
            baseline_response: Dictionary containing status_code, headers, content, elapsed_time
            mutated_response: Dictionary containing status_code, headers, content, elapsed_time

        Returns:
            DiffResult object containing detailed comparison
        """
        # Extract baseline values
        baseline_status = baseline_response.get('status_code')
        baseline_headers = baseline_response.get('headers', {})
        baseline_content = baseline_response.get('content', '')
        baseline_elapsed = baseline_response.get('elapsed_time', 0)

        # Extract mutated values
        mutated_status = mutated_response.get('status_code')
        mutated_headers = mutated_response.get('headers', {})
        mutated_content = mutated_response.get('content', '')
        mutated_elapsed = mutated_response.get('elapsed_time', 0)

        # Compare status codes
        status_code_changed = baseline_status != mutated_status

        # Compare headers
        headers_added, headers_removed, headers_changed_values = DiffEngine._compare_headers(
            baseline_headers, mutated_headers
        )
        headers_changed = bool(headers_added or headers_removed or headers_changed_values)

        # Compare body size
        baseline_size = len(baseline_content.encode('utf-8')) if isinstance(baseline_content, str) else len(baseline_content) if baseline_content else 0
        mutated_size = len(mutated_content.encode('utf-8')) if isinstance(mutated_content, str) else len(mutated_content) if mutated_content else 0
        body_size_changed = baseline_size != mutated_size
        body_size_delta = mutated_size - baseline_size

        # Compare body content
        body_content_changed, body_similarity = DiffEngine._compare_body_content(
            baseline_content, mutated_content
        )

        # Compare JSON if both responses appear to be JSON
        json_compared = False
        json_structure_changed = False
        json_values_changed = False
        json_keys_added = []
        json_keys_removed = []
        json_values_changed_details = []

        if DiffEngine._is_json_content(baseline_headers.get('Content-Type', '')) and \
           DiffEngine._is_json_content(mutated_headers.get('Content-Type', '')):
            try:
                baseline_json = json.loads(baseline_content) if baseline_content else {}
                mutated_json = json.loads(mutated_content) if mutated_content else {}

                json_compared = True
                json_structure_changed, json_values_changed, json_keys_added, json_keys_removed, json_values_changed_details = \
                    DiffEngine._compare_json_objects(baseline_json, mutated_json)
            except (json.JSONDecodeError, TypeError):
                # If JSON parsing fails, treat as regular content
                json_compared = False

        # Compare response times
        response_time_changed = baseline_elapsed != mutated_elapsed
        response_time_delta = mutated_elapsed - baseline_elapsed

        # Determine if there's a significant difference
        has_significant_difference = DiffEngine._is_significant_difference(
            status_code_changed,
            headers_changed,
            body_size_changed,
            body_content_changed,
            json_compared and (json_structure_changed or json_values_changed),
            response_time_changed
        )

        # Generate summary
        change_summary = DiffEngine._generate_summary(
            status_code_changed, baseline_status, mutated_status,
            headers_changed, len(headers_added), len(headers_removed), len(headers_changed_values),
            body_size_changed, body_size_delta,
            body_content_changed, body_similarity,
            json_compared, json_structure_changed, json_values_changed,
            response_time_changed, response_time_delta
        )

        return DiffResult(
            status_code_changed=status_code_changed,
            status_code_baseline=baseline_status,
            status_code_mutated=mutated_status,
            headers_changed=headers_changed,
            headers_added=headers_added,
            headers_removed=headers_removed,
            headers_changed_values=headers_changed_values,
            body_size_changed=body_size_changed,
            body_size_baseline=baseline_size,
            body_size_mutated=mutated_size,
            body_size_delta=body_size_delta,
            body_content_changed=body_content_changed,
            body_similarity=body_similarity,
            json_compared=json_compared,
            json_structure_changed=json_structure_changed,
            json_values_changed=json_values_changed,
            json_keys_added=json_keys_added,
            json_keys_removed=json_keys_removed,
            json_values_changed_details=json_values_changed_details,
            response_time_changed=response_time_changed,
            response_time_baseline=baseline_elapsed,
            response_time_mutated=mutated_elapsed,
            response_time_delta=response_time_delta,
            has_significant_difference=has_significant_difference,
            change_summary=change_summary
        )

    @staticmethod
    def _compare_headers(
        baseline: Dict[str, str],
        mutated: Dict[str, str]
    ) -> Tuple[List[str], List[str], List[Tuple[str, Any, Any]]]:
        """Compare two header dictionaries."""
        baseline_keys = set(baseline.keys())
        mutated_keys = set(mutated.keys())

        added = list(mutated_keys - baseline_keys)
        removed = list(baseline_keys - mutated_keys)

        changed_values = []
        common_keys = baseline_keys & mutated_keys
        for key in common_keys:
            if baseline[key] != mutated[key]:
                changed_values.append((key, baseline[key], mutated[key]))

        return added, removed, changed_values

    @staticmethod
    def _compare_body_content(baseline: str, mutated: str) -> Tuple[bool, float]:
        """Compare body content and return similarity ratio."""
        if baseline == mutated:
            return False, 1.0

        if not baseline and not mutated:
            return False, 1.0

        if not baseline or not mutated:
            return True, 0.0

        # Use difflib to calculate similarity
        matcher = difflib.SequenceMatcher(None, baseline, mutated)
        similarity = matcher.ratio()
        changed = similarity < 1.0

        return changed, similarity

    @staticmethod
    def _is_json_content(content_type: str) -> bool:
        """Check if content type indicates JSON."""
        return 'application/json' in content_type.lower()

    @staticmethod
    def _compare_json_objects(
        baseline: Any,
        mutated: Any,
        path: str = ""
    ) -> Tuple[bool, bool, List[str], List[str], List[Tuple[str, Any, Any]]]:
        """
        Compare two JSON objects recursively.

        Returns:
            (structure_changed, values_changed, keys_added, keys_removed, value_changes)
        """
        # Handle different types
        if type(baseline) != type(mutated):
            return True, True, [], [], [(path, baseline, mutated)]

        # Both are None
        if baseline is None and mutated is None:
            return False, False, [], [], []

        # Both are primitives (str, int, float, bool)
        if isinstance(baseline, (str, int, float, bool)) or baseline is None:
            if baseline == mutated:
                return False, False, [], [], []
            else:
                return False, True, [], [], [(path, baseline, mutated)]

        # Both are lists
        if isinstance(baseline, list) and isinstance(mutated, list):
            # For simplicity, we'll compare lengths and treat as value change if different
            # A more sophisticated implementation would do item-by-item comparison
            if len(baseline) != len(mutated):
                return True, True, [], [], [(path, baseline, mutated)]

            # Check each item
            structure_changed = False
            values_changed = False
            value_changes = []

            for i, (base_item, mut_item) in enumerate(zip(baseline, mutated)):
                item_path = f"{path}[{i}]"
                s_changed, v_changed, _, _, changes = DiffEngine._compare_json_objects(
                    base_item, mut_item, item_path
                )
                structure_changed = structure_changed or s_changed
                values_changed = values_changed or v_changed
                value_changes.extend(changes)

            return structure_changed, values_changed, [], [], value_changes

        # Both are dictionaries
        if isinstance(baseline, dict) and isinstance(mutated, dict):
            baseline_keys = set(baseline.keys())
            mutated_keys = set(mutated.keys())

            keys_added = list(mutated_keys - baseline_keys)
            keys_removed = list(baseline_keys - mutated_keys)

            structure_changed = bool(keys_added or keys_removed)

            # Check common keys
            values_changed = False
            value_changes = []

            common_keys = baseline_keys & mutated_keys
            for key in common_keys:
                new_path = f"{path}.{key}" if path else key
                s_changed, v_changed, _, _, changes = DiffEngine._compare_json_objects(
                    baseline[key], mutated[key], new_path
                )
                structure_changed = structure_changed or s_changed
                values_changed = values_changed or v_changed
                value_changes.extend(changes)

            return structure_changed, values_changed, keys_added, keys_removed, value_changes

        # Fallback for other types
        if baseline == mutated:
            return False, False, [], [], []
        else:
            return False, True, [], [], [(path, baseline, mutated)]

    @staticmethod
    def _is_significant_difference(
        status_changed: bool,
        headers_changed: bool,
        body_size_changed: bool,
        body_content_changed: bool,
        json_changed: bool,
        time_changed: bool
    ) -> bool:
        """Determine if differences are significant enough to report."""
        # Status code change is always significant
        if status_changed:
            return True

        # Significant header changes
        if headers_changed:
            return True

        # Significant body size change (more than 10% or 1KB)
        if body_size_changed:
            # This would need the actual sizes to be meaningful
            # For now, treat any size change as significant
            return True

        # Significant content change (less than 90% similar)
        if body_content_changed:
            return True

        # JSON changes are significant
        if json_changed:
            return True

        # Response time changes (more than 50% or 100ms)
        if time_changed:
            # This would need actual times to be meaningful
            # For now, treat any time change as significant
            return True

        return False

    @staticmethod
    def _generate_summary(
        status_changed: bool, baseline_status: Any, mutated_status: Any,
        headers_changed: bool, headers_added_count: int, headers_removed_count: int, headers_changed_count: int,
        body_size_changed: bool, body_size_delta: int,
        body_content_changed: bool, body_similarity: float,
        json_compared: bool, json_structure_changed: bool, json_values_changed: bool,
        time_changed: bool, time_delta: float
    ) -> str:
        """Generate a human-readable summary of the differences."""
        parts = []

        if status_changed:
            parts.append(f"Status: {baseline_status} → {mutated_status}")

        if headers_changed:
            changes = []
            if headers_added_count > 0:
                changes.append(f"+{headers_added_count}")
            if headers_removed_count > 0:
                changes.append(f"-{headers_removed_count}")
            if headers_changed_count > 0:
                changes.append(f"~{headers_changed_count}")
            parts.append(f"Headers: {' '.join(changes)}")

        if body_size_changed:
            parts.append(f"Size: {body_size_delta:+d} bytes")

        if body_content_changed:
            similarity_pct = int(body_similarity * 100)
            parts.append(f"Content: {similarity_pct}% similar")

        if json_compared:
            if json_structure_changed:
                parts.append("JSON structure: changed")
            if json_values_changed:
                parts.append("JSON values: changed")

        if time_changed:
            parts.append(f"Time: {time_delta:+.0f}ms")

        if not parts:
            return "No significant differences detected"

        return " | ".join(parts)