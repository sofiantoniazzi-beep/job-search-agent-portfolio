"""Sanitized Tracker synchronization contract.

New qualified canonical jobs are appended once. Rediscovered jobs refresh only
observation-owned fields when a Tracker row exists; a previously seen vacancy may be
absent because canonical persistence includes jobs that never qualified for Tracker.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

USER_MANAGED_FIELDS = {"Status", "Notes", "Application"}
OBSERVATION_UPDATE_FIELDS = {"Last Seen", "Source", "Source Job IDs"}


class TrackerBackend(Protocol):
    def list_rows(self) -> list[dict]: ...
    def append_row(self, row: dict) -> None: ...
    def update_row(self, job_id: str, updates: dict) -> None: ...


@dataclass
class InMemoryTracker:
    rows: list[dict] = field(default_factory=list)

    def list_rows(self) -> list[dict]:
        return [dict(row) for row in self.rows]

    def append_row(self, row: dict) -> None:
        if any(existing.get("Job ID") == row.get("Job ID") for existing in self.rows):
            raise ValueError(f"Duplicate canonical Job ID: {row.get('Job ID')}")
        self.rows.append(dict(row))

    def update_row(self, job_id: str, updates: dict) -> None:
        for row in self.rows:
            if row.get("Job ID") == job_id:
                row.update(updates)
                return
        raise KeyError(job_id)


def _prepare_new(row: dict) -> dict:
    result = dict(row)
    if not result.get("Job ID"):
        raise ValueError("Tracker rows require a canonical Job ID")
    result.setdefault("Status", "New")
    result.setdefault("Availability Status", "Active")
    result.setdefault("Notes", "")
    result.setdefault("Application", "")
    result["Last Seen"] = result.get("First Seen", result.get("Last Seen", ""))
    return result


def _prepare_seen_updates(row: dict) -> dict:
    return {field: row.get(field, "") for field in OBSERVATION_UPDATE_FIELDS if field in row}


def sync_tracker(jobs: list[dict], backend: TrackerBackend) -> dict:
    existing_ids = {str(row.get("Job ID", "")).strip() for row in backend.list_rows()}
    new_rows = updated_rows = previously_seen_absent = 0

    for row in jobs:
        job_id = str(row.get("Job ID", "")).strip()
        if not job_id:
            raise ValueError("Cannot sync a row without Job ID")

        status = row.get("Persistence Status")
        if status == "New":
            # A New persistence status colliding with an existing Tracker canonical ID
            # is a contradiction and must not silently overwrite human workflow state.
            if job_id in existing_ids:
                raise ValueError(f"New canonical vacancy already exists in Tracker: {job_id}")
            backend.append_row(_prepare_new(row))
            existing_ids.add(job_id)
            new_rows += 1
        elif status == "Previously Seen":
            if job_id in existing_ids:
                backend.update_row(job_id, _prepare_seen_updates(row))
                updated_rows += 1
            else:
                # Legitimate: the canonical vacancy may have been rejected before the
                # Tracker qualification gate on its original run.
                previously_seen_absent += 1
        else:
            raise ValueError(f"Unexpected Persistence Status: {status!r}")

    return {
        "new_rows": new_rows,
        "updated_rows": updated_rows,
        "previously_seen_absent": previously_seen_absent,
    }
