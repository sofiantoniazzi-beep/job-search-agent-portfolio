"""Sanitized orchestration of the production daily architecture.

The reference keeps infrastructure adapters injectable so the architecture remains
readable without exposing live credentials, spreadsheet IDs, cloud IDs, or candidate
data. Same-run deduplication and canonical identity resolution happen before the
new-vacancy decision engine, matching production behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable


@dataclass
class PipelineDependencies:
    retrieve: Callable[[], Iterable[dict]]
    normalize: Callable[[Iterable[dict]], list[dict]]
    cross_source_deduplicate: Callable[[list[dict]], list[dict]]
    resolve_persistence: Callable[[list[dict]], tuple[list[dict], dict]]
    process_new_vacancies: Callable[[list[dict]], list[dict]]
    sync_tracker: Callable[[list[dict]], dict]
    refresh_ranker: Callable[[], None]
    commit_state: Callable[[dict], None]
    checkpoint: Callable[[str, dict], None]
    write_run_log: Callable[[dict], None]


def run_daily_pipeline(deps: PipelineDependencies) -> dict:
    """Run retrieval -> operational sync while preserving the commit boundary."""
    raw = list(deps.retrieve())
    deps.checkpoint("retrieval", {"retrieved": len(raw)})

    normalized = deps.normalize(raw)
    deduped = deps.cross_source_deduplicate(normalized)
    canonical, pending_registry = deps.resolve_persistence(deduped)

    new_jobs = [job for job in canonical if job.get("Persistence Status") == "New"]
    previously_seen = [
        job for job in canonical if job.get("Persistence Status") == "Previously Seen"
    ]
    deps.checkpoint(
        "processing",
        {
            "normalized": len(normalized),
            "deduped": len(deduped),
            "canonical": len(canonical),
            "new_canonical": len(new_jobs),
            "previously_seen": len(previously_seen),
        },
    )

    # Production applies eligibility, geographic assessment, pre-ranking, gated
    # semantic assessment, and CV routing only to NEW canonical vacancies.
    qualified_new = deps.process_new_vacancies(new_jobs)

    # Previously seen vacancies bypass the decision engine. Tracker synchronization
    # may refresh observation metadata if a previously seen vacancy already has a
    # Tracker row; vacancies rejected on an earlier run may legitimately be absent.
    tracker_payload = qualified_new + previously_seen
    tracker_result = deps.sync_tracker(tracker_payload)
    deps.checkpoint("tracker_sync", tracker_result)

    deps.refresh_ranker()
    deps.checkpoint("ranker_refresh", {"refreshed": True})

    # Canonical state advances only after both downstream spreadsheet steps succeed.
    deps.commit_state(pending_registry)
    deps.checkpoint("state_commit", {"committed": True})

    summary = {
        "retrieved": len(raw),
        "normalized": len(normalized),
        "deduped": len(deduped),
        "canonical": len(canonical),
        "new_canonical": len(new_jobs),
        "previously_seen": len(previously_seen),
        "qualified_new": len(qualified_new),
        "tracker_new": int(tracker_result.get("new_rows", 0)),
        "tracker_updated": int(tracker_result.get("updated_rows", 0)),
    }
    deps.write_run_log(summary)
    return summary
