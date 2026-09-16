from datetime import date

import pytest

from src.application_workflow import move_to_application, ranker_rows
from src.availability import AvailabilityEvidence, absence_from_retrieval, aggregate_source_statuses, classify
from src.cloud_runner import CloudWorkflows, run_workflow
from src.cv_routing import route_cv
from src.deduplicate import is_duplicate
from src.expanded_assessment import deterministic_output, validate_model_payload
from src.matching import MatchScore, application_recommendation, wildcard_surfaces
from src.pipeline import PipelineDependencies, run_daily_pipeline
from src.tracker_writer import InMemoryTracker, sync_tracker
from src.weekly_availability import run_weekly_availability, select_backlog


def test_wildcard_threshold():
    assert wildcard_surfaces(MatchScore(36, 24, 12, 8))
    assert not wildcard_surfaces(MatchScore(35, 23, 12, 8))


def test_career_direction_guardrail():
    score = MatchScore(45, 30, 7, 10)
    assert score.base_match == 92
    assert application_recommendation(score) == "Consider"


def test_expanded_assessment_keeps_arithmetic_in_python():
    result = validate_model_payload({"responsibilities": 40, "skills": 25, "career_direction": 12, "seniority": 8, "domain_advantage": 4, "evidence": [], "gaps": [], "questions": [], "why": "Strong overlap"})
    output = deterministic_output(result)
    assert output["Base Match Score"] == 85
    assert output["Assessment"] == "Very Strong"
    assert output["Application"] == "Priority Apply"


def test_retrieval_absence_is_unknown():
    assert absence_from_retrieval() == "Unknown"


def test_generic_404_is_not_automatically_closed():
    assert classify(AvailabilityEvidence(http_status=404)) == "Unknown"


def test_himalayas_known_404_can_be_closed():
    assert classify(AvailabilityEvidence(source="Himalayas", http_status=404)) == "Closed"


def test_explicit_closure_is_closed():
    assert classify(AvailabilityEvidence(explicit_closed=True)) == "Closed"


def test_apply_control_is_active():
    assert classify(AvailabilityEvidence(apply_control=True)) == "Active"


def test_canonical_availability_aggregation():
    assert aggregate_source_statuses(["Closed", "Active"]) == "Active"
    assert aggregate_source_statuses(["Closed", "Closed"]) == "Closed"
    assert aggregate_source_statuses(["Closed", "Unknown"]) == "Unknown"


def test_cross_source_duplicate_rule():
    a = {"Source": "Source A", "Company": "Example Co.", "Job Title": "Product Manager", "Job Description": "Own product discovery and coordinate feature delivery with engineering.", "Location": "New York, NY"}
    b = {"Source": "Source B", "Company": "Example Co", "Job Title": "Product Manager", "Job Description": "Own product discovery and coordinate feature delivery with engineering.", "Location": "New York City, NY"}
    assert is_duplicate(a, b)


def test_weekly_backlog_skips_already_closed_rows():
    rows = [{"Job ID": "JOB-000001", "Availability Status": "Active"}, {"Job ID": "JOB-000002", "Availability Status": "Closed"}, {"Job ID": "", "Availability Status": "Active"}]
    assert [row["Job ID"] for row in select_backlog(rows)] == ["JOB-000001"]


def test_weekly_availability_updates_only_availability_fields():
    tracker = InMemoryTracker(rows=[{"Job ID": "JOB-000001", "Availability Status": "Active", "Last Seen": "2026-09-01", "Status": "Reviewing", "Notes": "Keep this note"}])
    result = run_weekly_availability(tracker=tracker, gather_evidence=lambda _: AvailabilityEvidence(explicit_closed=True))
    row = tracker.rows[0]
    assert result["closed"] == 1
    assert row["Availability Status"] == "Closed"
    assert row["Last Seen"] == "2026-09-01"
    assert row["Status"] == "Reviewing"
    assert row["Notes"] == "Keep this note"
    assert row["Last Availability Check"]


def test_weekly_cloud_workflow_does_not_commit_canonical_state():
    calls = []
    workflows = CloudWorkflows(daily=lambda: calls.append("daily"), weekly_availability=lambda: calls.append("availability") or "ok", download_state=lambda: calls.append("download"), upload_state=lambda: calls.append("upload"))
    assert run_workflow("availability", workflows) == "ok"
    assert calls == ["download", "availability"]


def test_daily_cloud_workflow_commits_after_success():
    calls = []
    workflows = CloudWorkflows(daily=lambda: calls.append("daily") or "ok", weekly_availability=lambda: calls.append("availability"), download_state=lambda: calls.append("download"), upload_state=lambda: calls.append("upload"))
    assert run_workflow("daily", workflows) == "ok"
    assert calls == ["download", "daily", "upload"]


def test_daily_pipeline_processes_only_new_and_commits_after_downstream_success():
    calls = []
    canonical = [{"Job ID": "JOB-000001", "Persistence Status": "New"}, {"Job ID": "JOB-000002", "Persistence Status": "Previously Seen"}]
    deps = PipelineDependencies(
        retrieve=lambda: [{"id": 1}, {"id": 2}],
        normalize=lambda jobs: list(jobs),
        cross_source_deduplicate=lambda jobs: jobs,
        resolve_persistence=lambda jobs: (canonical, {"registry": "pending"}),
        process_new_vacancies=lambda jobs: calls.append(("process", [j["Job ID"] for j in jobs])) or [dict(j, **{"Base Match Score": 85}) for j in jobs],
        sync_tracker=lambda jobs: calls.append(("tracker", [j["Job ID"] for j in jobs])) or {"new_rows": 1, "updated_rows": 1},
        refresh_ranker=lambda: calls.append(("ranker", None)),
        commit_state=lambda state: calls.append(("commit", state)),
        checkpoint=lambda stage, data: calls.append(("checkpoint", stage)),
        write_run_log=lambda summary: calls.append(("log", summary["canonical"])),
    )
    summary = run_daily_pipeline(deps)
    assert summary["new_canonical"] == 1
    assert ("process", ["JOB-000001"]) in calls
    assert next(call for call in calls if call[0] == "tracker")[1] == ["JOB-000001", "JOB-000002"]
    stages = [call[0] for call in calls]
    assert stages.index("tracker") < stages.index("ranker") < stages.index("commit")


def test_daily_pipeline_does_not_commit_if_tracker_sync_fails():
    committed = []
    deps = PipelineDependencies(
        retrieve=lambda: [{}], normalize=lambda jobs: list(jobs), cross_source_deduplicate=lambda jobs: jobs,
        resolve_persistence=lambda jobs: ([{"Job ID": "JOB-000001", "Persistence Status": "New"}], {"pending": 1}),
        process_new_vacancies=lambda jobs: jobs,
        sync_tracker=lambda jobs: (_ for _ in ()).throw(RuntimeError("sheet down")),
        refresh_ranker=lambda: None, commit_state=lambda state: committed.append(state), checkpoint=lambda stage, data: None, write_run_log=lambda summary: None,
    )
    with pytest.raises(RuntimeError):
        run_daily_pipeline(deps)
    assert committed == []


def test_previously_seen_missing_from_tracker_is_legitimate():
    tracker = InMemoryTracker(rows=[])
    result = sync_tracker([{"Job ID": "JOB-000123", "Persistence Status": "Previously Seen", "Last Seen": "2026-09-16"}], tracker)
    assert result["previously_seen_absent"] == 1
    assert tracker.rows == []


def test_cv_routing_function_first_examples():
    assert route_cv({"Job Title": "Solutions Consultant", "Job Description": "AI platform"})["CV Variant"] == "Product Specialist - General"
    assert route_cv({"Job Title": "Product Manager", "Role Family": "Product", "Job Description": "AI and LLM roadmap"})["CV Variant"] == "Product Manager - Technical & AI"
    assert route_cv({"Job Title": "Strategy Consultant", "Role Family": "Strategy", "Job Description": "AI transformation"})["CV Variant"] == "Consulting & Strategy - AI Consulting"


def test_ranker_filters_status_availability_and_uses_domain_tiebreak():
    jobs = [
        {"Job ID": "A", "Company": "A Co", "Status": "New", "Availability Status": "Active", "Base Match Score": 80, "Posted Date": "2026-09-14", "Domain Advantage": 2},
        {"Job ID": "B", "Company": "B Co", "Status": "Reviewing", "Availability Status": "Active", "Base Match Score": 80, "Posted Date": "2026-09-14", "Domain Advantage": 8},
        {"Job ID": "C", "Company": "C Co", "Status": "New", "Availability Status": "Closed", "Base Match Score": 100, "Posted Date": "2026-09-14", "Domain Advantage": 10},
    ]
    rows = ranker_rows(jobs, today=date(2026, 9, 14))
    assert [row["Job ID"] for row in rows] == ["B", "A"]
    moved = move_to_application(rows[0])
    assert moved["Status"] == "Applying"
    assert moved["Application"] == "To Apply"
