"""Portfolio-safe reference implementation of conservative cross-source deduplication."""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Optional

import pandas as pd

DESCRIPTION_THRESHOLD = 0.80

GENERIC_LOCATIONS = {
    "",
    "remote",
    "worldwide",
    "anywhere",
    "global",
    "united states",
    "usa",
    "us",
}

CITY_ALIASES = {
    "new york city": "new york",
    "nyc": "new york",
}


def normalize_text(value) -> str:
    if value is None or (not isinstance(value, str) and pd.isna(value)):
        return ""
    text = unicodedata.normalize("NFKD", str(value).lower().strip())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text)).strip()


def description_similarity(a, b) -> Optional[float]:
    a, b = normalize_text(a), normalize_text(b)
    return SequenceMatcher(None, a, b).ratio() if a and b else None


def specific_city(location) -> str:
    """Return a normalized specific city, treating common city aliases as equivalent."""
    normalized = normalize_text(location)
    if normalized in GENERIC_LOCATIONS:
        return ""

    first = normalize_text(str(location).split(",")[0])
    if first in GENERIC_LOCATIONS:
        return ""

    return CITY_ALIASES.get(first, first)


def is_duplicate(a: dict, b: dict) -> bool:
    """High-confidence rule: exact normalized company/title, similar JD, no city conflict."""
    if a.get("Source") == b.get("Source"):
        return False
    if normalize_text(a.get("Company")) != normalize_text(b.get("Company")):
        return False
    if normalize_text(a.get("Job Title")) != normalize_text(b.get("Job Title")):
        return False

    similarity = description_similarity(a.get("Job Description"), b.get("Job Description"))
    if similarity is None or similarity < DESCRIPTION_THRESHOLD:
        return False

    city_a, city_b = specific_city(a.get("Location", "")), specific_city(b.get("Location", ""))
    return not (city_a and city_b and city_a != city_b)


def find_duplicate_pairs(jobs: pd.DataFrame) -> pd.DataFrame:
    """Return qualifying cross-source pairs without destructively merging source rows."""
    rows = jobs.to_dict("records")
    pairs = []
    for i, a in enumerate(rows):
        for b in rows[i + 1:]:
            if is_duplicate(a, b):
                pairs.append({
                    "Job ID A": a.get("Job ID", ""),
                    "Job ID B": b.get("Job ID", ""),
                    "Company": a.get("Company", ""),
                    "Job Title": a.get("Job Title", ""),
                    "Description Similarity": description_similarity(
                        a.get("Job Description"), b.get("Job Description")
                    ),
                })
    return pd.DataFrame(pairs)
