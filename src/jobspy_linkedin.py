"""Sanitized LinkedIn retrieval adapter for the portfolio repository.

The production system uses a broader private search taxonomy. This example keeps only
three synthetic role queries and two locations: New York City and US Remote.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from jobspy import scrape_jobs

CONFIG_PATH = Path("config/search_profiles.example.json")
RESULTS_WANTED = 250
FETCH_DESCRIPTIONS = True


def load_search_config(path: Path = CONFIG_PATH) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def apply_work_model_overrides(jobs: pd.DataFrame) -> pd.DataFrame:
    """Correct only strong contradictions to an inferred Remote value."""
    if jobs.empty:
        return jobs.copy()

    corrected = jobs.copy()
    title = corrected.get("title", pd.Series("", index=corrected.index)).fillna("").astype(str).str.lower()
    description = corrected.get("description", pd.Series("", index=corrected.index)).fillna("").astype(str).str.lower()

    contradiction = (
        title.str.contains(r"\bhybrid\b|\bon[- ]?site\b|\bonsite\b", regex=True, na=False)
        | description.str.contains(
            r"\bhybrid schedule\b|\bhybrid role\b|\bon[- ]?site role\b|"
            r"\b\d+ days? (?:a|per) week in (?:the )?office\b",
            regex=True,
            na=False,
        )
    )

    currently_remote = corrected.get("is_remote", pd.Series(False, index=corrected.index)).fillna(False).eq(True)
    corrected.loc[currently_remote & contradiction, "is_remote"] = False
    return corrected


def filter_us_remote(jobs: pd.DataFrame) -> pd.DataFrame:
    if jobs.empty:
        return jobs.copy()
    return jobs[jobs.get("is_remote", False).fillna(False).eq(True)].copy()


def search_linkedin(config: dict | None = None) -> pd.DataFrame:
    config = config or load_search_config()
    hours_old = config.get("daily_hours_old") if config.get("run_mode") == "daily" else None

    searches = [
        (category, query, key, location)
        for category, queries in config["role_queries"].items()
        for query in queries
        for key, location in config["locations"].items()
    ]

    all_jobs: list[pd.DataFrame] = []
    for category, query, location_key, location in searches:
        kwargs = {
            "site_name": ["linkedin"],
            "search_term": query,
            "location": location["jobspy_location"],
            "results_wanted": RESULTS_WANTED,
            "hours_old": hours_old,
            "linkedin_fetch_description": FETCH_DESCRIPTIONS,
        }
        if location_key == "us_remote":
            kwargs["is_remote"] = True

        jobs = scrape_jobs(**kwargs)
        if jobs.empty:
            continue

        jobs = apply_work_model_overrides(jobs)
        if location_key == "us_remote":
            jobs = filter_us_remote(jobs)

        if jobs.empty:
            continue

        jobs["search_category"] = category
        jobs["search_query"] = query
        jobs["search_location"] = location["label"]
        all_jobs.append(jobs)

    return pd.concat(all_jobs, ignore_index=True) if all_jobs else pd.DataFrame()
