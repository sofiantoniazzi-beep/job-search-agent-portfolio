"""Sanitized run-checkpoint and recovery primitives."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def generate_run_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{timestamp}-{uuid4().hex[:8]}"


def file_sha256(path: str | Path) -> str | None:
    path = Path(path)
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def create_manifest(run_id: str, registry_path: str | Path) -> dict:
    return {
        "run_id": run_id,
        "base_registry_sha256": file_sha256(registry_path),
        "retrieval_completed": False,
        "processing_completed": False,
        "tracker_sync_completed": False,
        "ranker_refresh_completed": False,
        "state_committed": False,
        "run_log_completed": False,
        "counts": {},
    }


def save_manifest(manifest: dict, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def load_manifest(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def mark_stage(manifest: dict, stage: str, **updates) -> dict:
    result = dict(manifest)
    result[f"{stage}_completed"] = True
    result.update(updates)
    return result


def assert_registry_unchanged(manifest: dict, registry_path: str | Path) -> None:
    expected = manifest.get("base_registry_sha256")
    current = file_sha256(registry_path)
    if expected != current:
        raise RuntimeError(
            "Registry changed after this run began; refusing unsafe resume. "
            f"expected={expected!r}, current={current!r}"
        )
