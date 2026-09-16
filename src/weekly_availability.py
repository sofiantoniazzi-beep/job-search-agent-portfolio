"""Sanitized weekly availability workflow.

This workflow is intentionally separate from daily discovery. It never creates
canonical IDs, appends new Tracker rows, reruns semantic matching, routes CVs,
or mutates canonical vacancy state.

It only re-checks existing non-closed Tracker vacancies, classifies each as
Active / Closed / Unknown using conservative evidence, updates availability
fields, and optionally refreshes the Ranker.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Iterable

from .availability import AvailabilityEvidence, classify
from .tracker_writer import TrackerBackend


@dataclass(frozen=True)
class AvailabilityResult:
    job_id: str
    status: str
    checked_at: str


def select_backlog(rows: Iterable[dict]) -> list[dict]:
    """Check canonical Tracker rows that are not already Closed."""
    selected = []
    for row in rows:
        job_id = str(row.get("Job ID", "")).strip()
        availability = str(row.get("Availability Status", "")).strip()
        if job_id and availability != "Closed":
            selected.append(dict(row))
    return selected


def run_weekly_availability(
    *,
    tracker: TrackerBackend,
    gather_evidence: Callable[[dict], AvailabilityEvidence],
    refresh_ranker: Callable[[], object] | None = None,
) -> dict:
    """Execute the weekly availability-maintenance workflow.

    The caller supplies source-specific evidence gathering. This keeps the
    portfolio implementation free of live source URLs and production IDs while
    preserving the production transaction boundary and classification policy.
    """
    backlog = select_backlog(tracker.list_rows())
    checked_at = datetime.now(timezone.utc).isoformat()

    counts = {"Active": 0, "Closed": 0, "Unknown": 0}
    updates: list[AvailabilityResult] = []

    for row in backlog:
        evidence = gather_evidence(row)
        status = classify(evidence)
        job_id = str(row["Job ID"]).strip()

        # Weekly availability owns only availability fields. It deliberately
        # does not touch Last Seen, matching output, CV routing, Status, or Notes.
        tracker.update_row(
            job_id,
            {
                "Availability Status": status,
                "Last Availability Check": checked_at,
            },
        )

        counts[status] += 1
        updates.append(AvailabilityResult(job_id, status, checked_at))

    ranker_refreshed = False
    if refresh_ranker is not None and updates:
        refresh_ranker()
        ranker_refreshed = True

    return {
        "selected_rows": len(backlog),
        "checked_rows": len(updates),
        "active": counts["Active"],
        "closed": counts["Closed"],
        "unknown": counts["Unknown"],
        "ranker_refreshed": ranker_refreshed,
    }
