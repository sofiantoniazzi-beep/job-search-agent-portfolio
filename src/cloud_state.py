"""Portfolio-safe object-storage abstraction for durable state.

Production uses managed cloud object storage. This module shows the same boundary
without embedding provider-specific bucket names or credentials.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class ObjectStore(Protocol):
    def download(self, object_name: str, destination: Path) -> bool: ...
    def upload(self, source: Path, object_name: str) -> None: ...


STATE_FILES = (
    "vacancy_registry.json",
    "matching_checkpoint.json",
    "geographic_eligibility_cache.json",
)


def download_state(store: ObjectStore, state_dir: str | Path = "state") -> None:
    state_dir = Path(state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    for filename in STATE_FILES:
        store.download(filename, state_dir / filename)


def upload_state(store: ObjectStore, state_dir: str | Path = "state") -> None:
    """Commit durable state only after downstream synchronization succeeds."""
    state_dir = Path(state_dir)
    for filename in STATE_FILES:
        source = state_dir / filename
        if source.exists():
            store.upload(source, filename)


def upload_run_checkpoint(
    store: ObjectStore,
    run_id: str,
    runs_dir: str | Path = "state/runs",
) -> None:
    """Recovery checkpoints may be uploaded on success or failure."""
    root = Path(runs_dir) / run_id
    if not root.exists():
        return
    for source in root.rglob("*"):
        if source.is_file():
            relative = source.relative_to(Path(runs_dir)).as_posix()
            store.upload(source, f"runs/{relative}")
