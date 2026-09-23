"""Sanitized canonical-vacancy persistence reference.

Source observations retain provider aliases while downstream workflow uses stable
``JOB-######`` identities. Resolution is deliberately conservative: known aliases,
strict same-source reposts, then one unambiguous cross-source historical match.
"""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

from .deduplicate import DESCRIPTION_THRESHOLD, description_similarity, normalize_text, specific_city

REGISTRY_VERSION = 2
CANONICAL_PREFIX = "JOB-"
REPOST_WINDOW_DAYS = 60


def empty_registry() -> dict:
    return {"version": REGISTRY_VERSION, "next_job_number": 1, "vacancies": {}}


def load_registry(path: str | Path) -> dict:
    path = Path(path)
    if not path.exists():
        return empty_registry()
    registry = json.loads(path.read_text(encoding="utf-8"))
    if registry.get("version") != REGISTRY_VERSION:
        raise ValueError("Unsupported registry version")
    registry.setdefault("next_job_number", 1)
    registry.setdefault("vacancies", {})
    return registry


def save_registry(registry: dict, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(registry, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def _new_job_id(registry: dict) -> str:
    number = int(registry["next_job_number"])
    registry["next_job_number"] = number + 1
    return f"{CANONICAL_PREFIX}{number:06d}"


def _parse_date(value: object) -> date | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _source_set(value: object) -> set[str]:
    if isinstance(value, (list, tuple, set)):
        values = value
    else:
        values = str(value or "").split(";")
    return {normalize_text(v) for v in values if normalize_text(v)}


def _alias_index(registry: dict) -> dict[str, str]:
    index: dict[str, str] = {}
    for canonical_id, vacancy in registry["vacancies"].items():
        for alias in vacancy.get("source_aliases", []):
            if alias in index and index[alias] != canonical_id:
                raise ValueError(f"Alias owned by multiple canonical jobs: {alias}")
            index[alias] = canonical_id
    return index


def _same_identity_fields(row: pd.Series, vacancy: dict) -> bool:
    company = normalize_text(row.get("Company"))
    title = normalize_text(row.get("Job Title"))
    if not company or company != normalize_text(vacancy.get("company")):
        return False
    if not title or title != normalize_text(vacancy.get("job_title")):
        return False
    if _exact_remote_identity(row, vacancy):
        return True
    current_city = specific_city(row.get("Location", ""))
    historic_city = specific_city(vacancy.get("location", ""))
    return not (current_city and historic_city and current_city != historic_city)


def _exact_remote_identity(row: pd.Series, vacancy: dict) -> bool:
    """An identical remote advertisement may carry different city labels."""
    if normalize_text(row.get("Work Model")) != "remote":
        return False
    if normalize_text(vacancy.get("work_model")) not in {"", "remote"}:
        return False
    current = normalize_text(row.get("Job Description"))
    return bool(current and current == normalize_text(vacancy.get("job_description")))


def _strict_repost_match(row: pd.Series, vacancy: dict) -> bool:
    current_source = normalize_text(row.get("Source"))
    historic_sources = _source_set(vacancy.get("sources") or vacancy.get("source"))
    if not current_source or current_source not in historic_sources:
        return False
    if not _same_identity_fields(row, vacancy):
        return False
    if normalize_text(row.get("Job Description")) != normalize_text(vacancy.get("job_description")):
        return False
    last_seen = _parse_date(vacancy.get("last_seen"))
    observed = _parse_date(row.get("First Seen")) or datetime.now(timezone.utc).date()
    return bool(last_seen and 0 <= (observed - last_seen).days <= REPOST_WINDOW_DAYS)


def _cross_source_historical_match(row: pd.Series, vacancy: dict) -> bool:
    """Conservative historical match used only when exactly one candidate qualifies."""
    if not _same_identity_fields(row, vacancy):
        return False
    similarity = description_similarity(row.get("Job Description"), vacancy.get("job_description"))
    if similarity is None or similarity < DESCRIPTION_THRESHOLD:
        return False
    current_sources = _source_set(row.get("Source"))
    historic_sources = _source_set(vacancy.get("sources") or vacancy.get("source"))
    # Historical cross-source resolution requires genuinely new source provenance.
    return bool(current_sources and not current_sources.issubset(historic_sources))


def resolve_canonical_jobs(jobs: pd.DataFrame, registry: dict) -> tuple[pd.DataFrame, dict]:
    """Resolve observations without mutating the supplied registry.

    A frozen historical snapshot is used for fuzzy historical matching so records
    created earlier in the same run cannot become accidental historical candidates.
    """
    working = deepcopy(registry)
    historical_registry = deepcopy(registry)
    aliases = _alias_index(working)
    rows: list[dict] = []

    for _, row in jobs.iterrows():
        source_alias = str(row.get("Job ID", "") or "").strip()
        canonical_id = aliases.get(source_alias)
        match_reason = "Known source alias" if canonical_id else ""

        if not canonical_id:
            reposts = [
                cid for cid, vacancy in historical_registry["vacancies"].items()
                if _strict_repost_match(row, vacancy)
            ]
            if len(reposts) == 1:
                canonical_id = reposts[0]
                match_reason = "Strict same-source repost match"
            elif len(reposts) > 1:
                raise ValueError("Ambiguous same-source repost match; refusing silent merge")

        if not canonical_id:
            cross_source = [
                cid for cid, vacancy in historical_registry["vacancies"].items()
                if _cross_source_historical_match(row, vacancy)
            ]
            if len(cross_source) == 1:
                canonical_id = cross_source[0]
                match_reason = "Conservative cross-source historical match"
            elif len(cross_source) > 1:
                # Ambiguity is not an error: production favors a new canonical vacancy
                # over a destructive false merge when identity is uncertain.
                canonical_id = None

        status = "Previously Seen"
        if not canonical_id:
            canonical_id = _new_job_id(working)
            status = "New"
            match_reason = "New canonical vacancy"
            working["vacancies"][canonical_id] = {
                "company": row.get("Company", ""),
                "job_title": row.get("Job Title", ""),
                "job_description": row.get("Job Description", ""),
                "location": row.get("Location", ""),
                "work_model": row.get("Work Model", ""),
                "first_seen": row.get("First Seen", ""),
                "last_seen": row.get("First Seen", ""),
                "sources": [],
                "source_aliases": [],
                "source_urls": {},
            }

        vacancy = working["vacancies"][canonical_id]
        source = str(row.get("Source", "") or "").strip()
        vacancy.setdefault("sources", [])
        if source and source not in vacancy["sources"]:
            vacancy["sources"].append(source)
        vacancy.setdefault("source_aliases", [])
        if source_alias and source_alias not in vacancy["source_aliases"]:
            vacancy["source_aliases"].append(source_alias)
            aliases[source_alias] = canonical_id
        vacancy.setdefault("source_urls", {})
        source_url = str(row.get("Job URL", "") or row.get("Application URL", "") or "").strip()
        if source_alias and source_url:
            vacancy["source_urls"][source_alias] = source_url
        vacancy["last_seen"] = row.get("First Seen", "") or vacancy.get("last_seen", "")

        result = row.to_dict()
        result["Job ID"] = canonical_id
        result["Source Aliases"] = "; ".join(vacancy["source_aliases"])
        result["Persistence Status"] = status
        result["Persistence Match Reason"] = match_reason
        rows.append(result)

    return pd.DataFrame(rows), working
