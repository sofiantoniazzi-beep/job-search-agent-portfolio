"""Sanitized expanded semantic-assessment boundary.

The model supplies bounded semantic judgments and evidence. Python validates those
judgments and owns arithmetic/classification so model authority remains constrained.
"""

from __future__ import annotations

from dataclasses import dataclass

from .matching import MatchScore, application_recommendation, assessment_label


@dataclass(frozen=True)
class AssessmentResult:
    score: MatchScore
    evidence: tuple[str, ...] = ()
    gaps: tuple[str, ...] = ()
    questions: tuple[str, ...] = ()
    why: str = ""


def validate_model_payload(payload: dict) -> AssessmentResult:
    score = MatchScore(
        responsibilities=payload.get("responsibilities"),
        skills=payload.get("skills"),
        career_direction=payload.get("career_direction"),
        seniority=payload.get("seniority"),
        domain_advantage=payload.get("domain_advantage", 0),
    )
    score.validate()

    def _strings(name: str) -> tuple[str, ...]:
        value = payload.get(name, [])
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise ValueError(f"{name} must be a list of strings")
        return tuple(value)

    why = payload.get("why", "")
    if not isinstance(why, str):
        raise ValueError("why must be a string")

    return AssessmentResult(
        score=score,
        evidence=_strings("evidence"),
        gaps=_strings("gaps"),
        questions=_strings("questions"),
        why=why,
    )


def deterministic_output(result: AssessmentResult) -> dict:
    """Convert validated semantic judgment into code-owned workflow outputs."""
    return {
        "Base Match Score": result.score.base_match,
        "Assessment": assessment_label(result.score.base_match),
        "Application": application_recommendation(result.score),
        "Domain Advantage": result.score.domain_advantage,
        "Evidence": list(result.evidence),
        "Gaps": list(result.gaps),
        "Questions": list(result.questions),
        "Why": result.why,
    }
