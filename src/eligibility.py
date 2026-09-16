"""Sanitized deterministic eligibility boundary.

Production uses hard exclusions only for high-confidence incompatibilities. Ambiguous
cases continue to later scoring: filter certainty, score ambiguity.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EligibilityDecision:
    eligible: bool
    reason: str


def evaluate_hard_exclusions(job: dict) -> EligibilityDecision:
    """Reference contract for candidate-configured deterministic exclusions.

    Real deployments should derive concrete geography/language/role rules from the
    user's Phase 0 configuration rather than copying another candidate's constraints.
    """
    flags = set(job.get("Hard Exclusion Flags", []) or [])
    supported = {
        "incompatible_geography",
        "freelance_or_gig",
        "internship_or_trainee",
        "explicit_entry_level_only",
        "strongly_technical_engineering_role",
        "clear_support_or_service_desk",
        "unsupported_required_language",
    }
    matched = sorted(flags & supported)
    if matched:
        return EligibilityDecision(False, "; ".join(matched))
    return EligibilityDecision(True, "No high-confidence hard exclusion")
