"""Sanitized operational run logging.

The production system writes this information to a dedicated Run Log worksheet.
This portfolio module keeps the record shape and cost-accounting rule visible while
using a backend protocol so no live spreadsheet identifiers are required.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class RunLogBackend(Protocol):
    def append(self, record: dict) -> None: ...


@dataclass
class ListRunLog:
    records: list[dict]

    def append(self, record: dict) -> None:
        self.records.append(dict(record))


def build_run_record(
    *,
    run_id: str,
    started_at: str,
    completed_at: str,
    status: str,
    raw_counts: dict,
    canonical_count: int,
    new_count: int,
    previously_seen_count: int,
    tracker_result: dict | None,
    ranker_refreshed: bool,
    anthropic_cost_usd: float | None = None,
    mistral_cost_usd: float | None = None,
    notes: str = "",
) -> dict:
    tracker_result = tracker_result or {}
    total_cost = None
    if anthropic_cost_usd is not None and mistral_cost_usd is not None:
        total_cost = anthropic_cost_usd + mistral_cost_usd

    return {
        "Run ID": run_id,
        "Started At": started_at,
        "Completed At": completed_at,
        "Status": status,
        "LinkedIn Retrieved": int(raw_counts.get("linkedin", 0)),
        "Indeed Retrieved": int(raw_counts.get("indeed", 0)),
        "Himalayas Retrieved": int(raw_counts.get("himalayas", 0)),
        "Canonical / Deduped": int(canonical_count),
        "New": int(new_count),
        "Previously Seen": int(previously_seen_count),
        "Tracker New": int(tracker_result.get("new_rows", 0)),
        "Tracker Updated": int(tracker_result.get("updated_rows", 0)),
        "Ranker Refreshed": bool(ranker_refreshed),
        "Anthropic Cost (USD)": anthropic_cost_usd,
        "Mistral Cost (USD)": mistral_cost_usd,
        "Total Cost (USD)": total_cost,
        "Error / Notes": notes,
    }


def append_run_log(backend: RunLogBackend, **kwargs) -> dict:
    record = build_run_record(**kwargs)
    backend.append(record)
    return record
