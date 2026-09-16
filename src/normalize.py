"""Shared normalization for the sanitized portfolio retrieval adapters.

Source-specific records are mapped into one common schema before persistence,
cross-source deduplication, eligibility, and semantic matching.
"""

from __future__ import annotations

from datetime import datetime, timezone
from html.parser import HTMLParser

import pandas as pd


class HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.parts.append(data.strip())


def clean_html(value: object) -> str:
    if not value:
        return ""
    parser = HTMLTextExtractor()
    try:
        parser.feed(str(value))
        return " ".join(parser.parts)
    except Exception:
        return str(value)


def clean_scalar(value: object) -> object:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return value


def normalize_date(value: object) -> str:
    value = clean_scalar(value)
    if value == "":
        return ""
    parsed = pd.to_datetime(value, errors="coerce", utc=True)
    return str(value) if pd.isna(parsed) else parsed.date().isoformat()


def join_values(values: object) -> str:
    if not values:
        return ""
    if isinstance(values, list):
        return "; ".join(str(value).strip() for value in values if value)
    return str(values).strip()


def first_nonblank(series: pd.Series) -> object:
    for value in series:
        value = clean_scalar(value)
        if str(value).strip():
            return value
    return ""


def join_unique(series: pd.Series) -> str:
    output: list[str] = []
    for value in series:
        text = str(clean_scalar(value)).strip()
        if text and text not in output:
            output.append(text)
    return "; ".join(output)


def aggregate_jobspy(df: pd.DataFrame) -> pd.DataFrame:
    if "id" not in df.columns:
        raise ValueError("JobSpy normalization requires an 'id' column")
    aggregation = {
        column: (join_unique if column in {"search_query", "matched_keywords"} else first_nonblank)
        for column in df.columns
        if column != "id"
    }
    return df.groupby("id", as_index=False, dropna=False).agg(aggregation)


def normalize_jobspy(df: pd.DataFrame, source: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    jobs = aggregate_jobspy(df.copy())
    now = datetime.now(timezone.utc)
    rows: list[dict] = []

    for _, job in jobs.iterrows():
        source_id = clean_scalar(job.get("id", ""))
        search_query = str(clean_scalar(job.get("search_query", ""))).strip()
        matched = str(clean_scalar(job.get("matched_keywords", ""))).strip()
        is_remote = clean_scalar(job.get("is_remote", ""))

        rows.append({
            "Job ID": f"{source.lower()}:{source_id}" if source_id != "" else "",
            "Source": source,
            "Source Job IDs": str(source_id),
            "Job URL": clean_scalar(job.get("job_url", "")),
            "Job Title": clean_scalar(job.get("title", "")),
            "Company": clean_scalar(job.get("company", "")),
            "Location": clean_scalar(job.get("location", "")),
            "Work Model": "Remote" if is_remote is True else ("Hybrid / On-site" if is_remote is False else ""),
            "Posted Date": normalize_date(job.get("date_posted", "")),
            "First Seen": now.date().isoformat(),
            "Job Description": clean_scalar(job.get("description", "")),
            "Application URL": clean_scalar(job.get("job_url_direct", "")),
            "Search Query / Keyword": search_query or matched,
            "Status": "New",
            "Ingestion Timestamp": now.isoformat(),
        })

    return pd.DataFrame(rows)


def normalize_linkedin(df: pd.DataFrame) -> pd.DataFrame:
    return normalize_jobspy(df, "LinkedIn")


def normalize_indeed(df: pd.DataFrame) -> pd.DataFrame:
    return normalize_jobspy(df, "Indeed")


def normalize_himalayas(jobs: list[dict]) -> pd.DataFrame:
    now = datetime.now(timezone.utc)
    rows: list[dict] = []
    for job in jobs:
        guid = job.get("guid") or ""
        pub_date = ""
        if job.get("pubDate"):
            try:
                pub_date = datetime.fromtimestamp(float(job["pubDate"]), tz=timezone.utc).date().isoformat()
            except (TypeError, ValueError, OSError):
                pass
        rows.append({
            "Job ID": f"himalayas:{guid}" if guid else "",
            "Source": "Himalayas",
            "Source Job IDs": guid,
            "Job URL": job.get("applicationLink") or "",
            "Job Title": job.get("title") or "",
            "Company": job.get("companyName") or "",
            "Location": "Remote",
            "Work Model": "Remote",
            "Remote Restrictions": join_values(job.get("locationRestrictions")),
            "Posted Date": pub_date,
            "First Seen": now.date().isoformat(),
            "Job Description": clean_html(job.get("description")),
            "Application URL": job.get("applicationLink") or "",
            "Search Query / Keyword": join_values(job.get("_search_queries")),
            "Skills / Categories": join_values(job.get("categories")),
            "Status": "New",
            "Ingestion Timestamp": now.isoformat(),
        })
    return pd.DataFrame(rows)


def combine_normalized_sources(linkedin: pd.DataFrame, indeed: pd.DataFrame, himalayas: pd.DataFrame) -> pd.DataFrame:
    frames = [frame for frame in (linkedin, indeed, himalayas) if not frame.empty]
    return pd.concat(frames, ignore_index=True, sort=False).fillna("") if frames else pd.DataFrame()
