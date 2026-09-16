"""Sanitized Google Sheets Ranker / application-workflow rules."""

from __future__ import annotations

import math
from datetime import date, datetime

REVIEWABLE_STATUSES = {"New", "Reviewing"}
FRESHNESS_HALF_LIFE_DAYS = 14


def _parse_date(value: object) -> date | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def freshness_score(posted_date: object, first_seen: object = None, today: date | None = None) -> float:
    """Production reference: Posted Date starts at 100; First Seen fallback at 50."""
    today = today or date.today()
    observed = _parse_date(posted_date)
    starting_score = 100.0
    if not observed:
        observed = _parse_date(first_seen)
        starting_score = 50.0
    if not observed:
        return 50.0
    age_days = max(0, (today - observed).days)
    return starting_score * math.pow(0.5, age_days / FRESHNESS_HALF_LIFE_DAYS)


def ranking_score(job: dict, today: date | None = None) -> float:
    base_match = float(job.get("Base Match Score", 0) or 0)
    freshness = freshness_score(job.get("Posted Date"), job.get("First Seen"), today=today)
    return round(0.70 * base_match + 0.30 * freshness, 2)


def ranker_rows(jobs: list[dict], today: date | None = None) -> list[dict]:
    rows: list[dict] = []
    for job in jobs:
        if job.get("Status") not in REVIEWABLE_STATUSES:
            continue
        if str(job.get("Availability Status", "")).strip() == "Closed":
            continue
        if job.get("Base Match Score") in {None, ""}:
            continue
        row = dict(job)
        row["Ranking Score"] = ranking_score(job, today=today)
        rows.append(row)

    rows.sort(
        key=lambda row: (
            -float(row.get("Ranking Score", 0) or 0),
            -float(row.get("Domain Advantage", 0) or 0),
            str(row.get("Company", "")).lower(),
        )
    )
    return rows


def move_to_application(job: dict) -> dict:
    if job.get("Status") not in REVIEWABLE_STATUSES:
        raise ValueError("Only New/Reviewing jobs can move into the application workflow")
    result = dict(job)
    result["Status"] = "Applying"
    result["Application"] = result.get("Application") or "To Apply"
    return result
