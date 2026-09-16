"""Sanitized Indeed retrieval adapter.

Demonstrates two deliberately different retrieval strategies:
- NYC: targeted role searches.
- US Remote: broad remote retrieval followed by a local discovery-keyword filter.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from jobspy import scrape_jobs

CONFIG_PATH = Path("config/search_profiles.example.json")
RESULTS_WANTED = 250


def load_search_config(path: Path = CONFIG_PATH) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def role_keywords(config: dict) -> list[str]:
    return [query.lower() for queries in config["role_queries"].values() for query in queries]


def find_matching_keywords(row: pd.Series, keywords: list[str]) -> list[str]:
    text = f"{row.get('title', '') or ''} {row.get('description', '') or ''}".lower()
    return [keyword for keyword in keywords if keyword in text]


def filter_by_posted_age(jobs: pd.DataFrame, hours: int) -> pd.DataFrame:
    """Retain missing dates; persistence is the authority on genuinely new jobs."""
    if jobs.empty or "date_posted" not in jobs.columns:
        return jobs.copy()
    posted = pd.to_datetime(jobs["date_posted"], errors="coerce", utc=True)
    cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(hours=hours)
    return jobs.loc[posted.isna() | (posted >= cutoff)].copy()


def search_nyc(config: dict) -> list[pd.DataFrame]:
    results: list[pd.DataFrame] = []
    hours_old = config.get("daily_hours_old") if config.get("run_mode") == "daily" else None
    location = config["locations"]["nyc"]

    for category, queries in config["role_queries"].items():
        for query in queries:
            jobs = scrape_jobs(
                site_name=["indeed"],
                search_term=f'"{query}"',
                location=location["jobspy_location"],
                country_indeed="USA",
                results_wanted=RESULTS_WANTED,
                hours_old=hours_old,
            )
            if jobs.empty:
                continue
            jobs["search_category"] = category
            jobs["search_query"] = query
            jobs["search_location"] = location["label"]
            results.append(jobs)
    return results


def search_us_remote(config: dict) -> pd.DataFrame:
    location = config["locations"]["us_remote"]
    jobs = scrape_jobs(
        site_name=["indeed"],
        search_term="",
        location=location["jobspy_location"],
        country_indeed="USA",
        results_wanted=RESULTS_WANTED,
        hours_old=None,
        is_remote=True,
    )
    if jobs.empty:
        return jobs

    if config.get("run_mode") == "daily":
        jobs = filter_by_posted_age(jobs, config["daily_hours_old"])

    keywords = role_keywords(config)
    jobs = jobs.copy()
    jobs["matched_keywords"] = jobs.apply(lambda row: find_matching_keywords(row, keywords), axis=1)
    jobs = jobs[jobs["matched_keywords"].map(bool)].copy()
    jobs["matched_keywords"] = jobs["matched_keywords"].apply(lambda values: " | ".join(values))
    jobs["search_category"] = "Broad Remote Discovery"
    jobs["search_query"] = ""
    jobs["search_location"] = location["label"]
    return jobs


def search_indeed(config: dict | None = None) -> pd.DataFrame:
    config = config or load_search_config()
    all_jobs = search_nyc(config)
    remote = search_us_remote(config)
    if not remote.empty:
        all_jobs.append(remote)
    return pd.concat(all_jobs, ignore_index=True) if all_jobs else pd.DataFrame()
