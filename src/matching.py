"""Portfolio reference for validated semantic-match scoring."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MatchScore:
    responsibilities: int
    skills: int
    career_direction: int
    seniority: int
    domain_advantage: int = 0

    @property
    def base_match(self) -> int:
        return self.responsibilities + self.skills + self.career_direction + self.seniority

    def validate(self) -> None:
        ranges = {
            "responsibilities": (self.responsibilities, 0, 45),
            "skills": (self.skills, 0, 30),
            "career_direction": (self.career_direction, 0, 15),
            "seniority": (self.seniority, 0, 10),
            "domain_advantage": (self.domain_advantage, 0, 10),
        }
        for name, (value, minimum, maximum) in ranges.items():
            if not isinstance(value, int) or not minimum <= value <= maximum:
                raise ValueError(f"{name} must be an integer from {minimum} to {maximum}")


def assessment_label(base_match: int) -> str:
    if base_match >= 90:
        return "Exceptional"
    if base_match >= 80:
        return "Very Strong"
    if base_match >= 75:
        return "Strong"
    if base_match >= 65:
        return "Possible"
    return "Weak"


def application_recommendation(score: MatchScore) -> str:
    score.validate()
    if score.career_direction <= 7:
        return "Consider" if score.base_match >= 65 else "Skip"
    if score.base_match >= 80:
        return "Priority Apply"
    if score.base_match >= 75:
        return "Apply"
    if score.base_match >= 65:
        return "Consider"
    return "Skip"


def wildcard_surfaces(score: MatchScore) -> bool:
    """Adjacent/unknown role titles may surface only at Base Match >= 80."""
    score.validate()
    return score.base_match >= 80
