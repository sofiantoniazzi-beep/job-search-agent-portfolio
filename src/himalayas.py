"""Sanitized Himalayas remote-job retrieval adapter.

Himalayas is remote-only, so this portfolio example represents the US Remote
search profile. Missing metadata survives hard filters unless it proves an
explicit exclusion.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import requests

API_URL = "https://himalayas.app/jobs/api/search"
CONFIG_PATH = Path("config/search_profiles.example.json")
MAX_PAGES = 3
EXCLUDED_EMPLOYMENT_TYPES = {"Part Time", "Intern", "Volunteer"}


def load_search_config(path: Path = CONFIG_PATH) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def search_jobs(query: str, page: int = 1) -> dict:
    response = requests.get(API_URL, params={"q": query, "page": page}, timeout=30)
    response.raise_for_status()
    return response.json()


def passes_recency(job: dict, cutoff_hours: int | None) -> bool:
    if cutoff_hours is None or not job.get("pubDate"):
        return True
    try:
        published = datetime.fromtimestamp(float(job["pubDate"]), tz=timezone.utc)
    except (TypeError, ValueError, OSError):
        return True
    age = (datetime.now(timezone.utc) - published).total_seconds()
    return age < 0 or age <= cutoff_hours * 3600


def passes_hard_filters(job: dict) -> bool:
    employment_type = job.get("employmentType")
    if employment_type in EXCLUDED_EMPLOYMENT_TYPES:
        return False

    restrictions = job.get("locationRestrictions")
    if restrictions and isinstance(restrictions, list):
        allowed = {str(value).strip().lower() for value in restrictions if value}
        if allowed and not ({"united states", "usa", "us"} & allowed):
            return False

    seniority = job.get("seniority")
    if isinstance(seniority, list) and len(seniority) == 1 and str(seniority[0]).lower() == "entry-level":
        return False

    return True


def deduplicate_jobs(jobs: list[dict]) -> list[dict]:
    unique: dict[str, dict] = {}
    for job in jobs:
        key = str(job.get("guid") or (job.get("companyName"), job.get("title"), job.get("applicationLink")))
        if key not in unique:
            unique[key] = job
        else:
            existing = unique[key].get("_search_queries", [])
            incoming = job.get("_search_queries", [])
            unique[key]["_search_queries"] = sorted(set(existing + incoming))
    return list(unique.values())


def search_himalayas(config: dict | None = None) -> list[dict]:
    config = config or load_search_config()
    cutoff = config.get("daily_hours_old") if config.get("run_mode") == "daily" else None
    queries = [query for values in config["role_queries"].values() for query in values]

    raw_jobs: list[dict] = []
    for query in queries:
        for page in range(1, MAX_PAGES + 1):
            jobs = search_jobs(query, page).get("jobs", [])
            if not jobs:
                break
            for job in jobs:
                job["_search_queries"] = [query]
            raw_jobs.extend(jobs)

    filtered = [job for job in raw_jobs if passes_recency(job, cutoff) and passes_hard_filters(job)]
    return deduplicate_jobs(filtered)
