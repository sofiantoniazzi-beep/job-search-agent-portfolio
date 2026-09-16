"""Sanitized source-aware vacancy availability classification.

The production policy prefers Unknown over a destructive false Closed result, while
allowing source-specific affirmative closure evidence where it is reliable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

Availability = Literal["Active", "Closed", "Unknown"]


@dataclass(frozen=True)
class AvailabilityEvidence:
    source: str = ""
    found_in_current_retrieval: bool = False
    explicit_closed: bool = False
    expired: bool = False
    apply_control: bool = False
    recognizable_job_page: bool = False
    redirected_to_search: bool = False
    http_status: Optional[int] = None
    auth_or_challenge: bool = False


def classify(evidence: AvailabilityEvidence) -> Availability:
    """Classify evidence without turning weak/temporary signals into closure."""
    source = evidence.source.strip().lower()

    if evidence.explicit_closed or evidence.expired:
        return "Closed"
    if evidence.auth_or_challenge:
        return "Unknown"
    if evidence.http_status in {401, 403, 429}:
        return "Unknown"
    if evidence.http_status is not None and evidence.http_status >= 500:
        return "Unknown"

    if source == "himalayas":
        if evidence.found_in_current_retrieval:
            return "Active"
        if evidence.http_status in {404, 410} or evidence.redirected_to_search:
            return "Closed"
        return "Unknown"

    if source == "indeed":
        if evidence.found_in_current_retrieval:
            return "Active"
        # Absence from the finite retrieval pool is never closure evidence.
        return "Unknown"

    if source == "linkedin":
        if evidence.apply_control and evidence.recognizable_job_page:
            return "Active"
        # LinkedIn 404/410 and recognizable pages without Apply remain ambiguous.
        return "Unknown"

    if evidence.apply_control:
        return "Active"
    return "Unknown"


def aggregate_source_statuses(statuses: list[Availability]) -> Availability:
    """ANY Active -> Active; ALL Closed -> Closed; otherwise Unknown."""
    if any(status == "Active" for status in statuses):
        return "Active"
    if statuses and all(status == "Closed" for status in statuses):
        return "Closed"
    return "Unknown"


def absence_from_retrieval() -> Availability:
    return "Unknown"
