"""Sanitized direct Google Sheets Ranker refresh boundary.

Production refreshes the scheduled Ranker directly from Python after Tracker sync.
Google Apps Script may still support interactive spreadsheet behavior, but it is not
the production scheduled-refresh transport. Live spreadsheet IDs are configuration.
"""

from __future__ import annotations

from typing import Protocol


BASE_MATCH_WEIGHT = 0.85
FRESHNESS_WEIGHT = 0.15


class SheetsBackend(Protocol):
    def read_tracker_rows(self) -> list[dict]: ...
    def replace_ranker_values(self, rows: list[dict]) -> None: ...


def refresh_ranker(backend: SheetsBackend, build_ranker_rows) -> dict:
    """Rebuild the derived Ranker while leaving sheet formatting to the backend.

    A production adapter can clear/replace only the Ranker value range so formatting,
    validation, and interactive spreadsheet behavior remain intact.
    """
    tracker_rows = backend.read_tracker_rows()
    ranker_rows = build_ranker_rows(tracker_rows)
    backend.replace_ranker_values(ranker_rows)
    return {"refreshed": True, "rows": len(ranker_rows)}
