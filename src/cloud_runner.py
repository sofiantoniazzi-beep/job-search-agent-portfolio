"""Sanitized cloud-aware workflow dispatcher.

The production system deploys daily discovery and weekly availability as
separate scheduled cloud jobs. This module demonstrates that separation without
including live cloud project IDs, scheduler names, or bucket identifiers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass
class CloudWorkflows:
    daily: Callable[[], object]
    weekly_availability: Callable[[], object]
    download_state: Callable[[], None] | None = None
    upload_state: Callable[[], None] | None = None


def run_workflow(name: str, workflows: CloudWorkflows) -> object:
    """Dispatch one scheduled workflow with distinct state semantics.

    Daily discovery may advance canonical state, but only after the daily
    pipeline succeeds. Weekly availability reads canonical state for source
    identity/provenance when needed, but never commits a new registry.
    """
    workflow = name.strip().lower()
    if workflow not in {"daily", "availability"}:
        raise ValueError("workflow must be 'daily' or 'availability'")

    if workflows.download_state is not None:
        workflows.download_state()

    if workflow == "availability":
        # Separate weekly maintenance path: no canonical-state upload.
        return workflows.weekly_availability()

    result = workflows.daily()

    # Canonical state moves forward only after a successful daily execution.
    if workflows.upload_state is not None:
        workflows.upload_state()

    return result
