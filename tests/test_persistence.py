import pandas as pd

from src.persistence import empty_registry, resolve_canonical_jobs


def make_job(alias: str, first_seen: str = "2026-09-01", location: str = "New York, NY", source: str = "LinkedIn") -> dict:
    return {
        "Job ID": alias,
        "Source": source,
        "Company": "Example Co",
        "Job Title": "Product Manager",
        "Job Description": "Own product roadmap and discovery.",
        "Location": location,
        "First Seen": first_seen,
        "Job URL": f"https://example.invalid/{alias}",
    }


def test_new_then_known_alias_is_previously_seen():
    first, registry = resolve_canonical_jobs(pd.DataFrame([make_job("linkedin:1")]), empty_registry())
    assert first.iloc[0]["Job ID"] == "JOB-000001"
    assert first.iloc[0]["Persistence Status"] == "New"
    second, _ = resolve_canonical_jobs(pd.DataFrame([make_job("linkedin:1", first_seen="2026-09-02")]), registry)
    assert second.iloc[0]["Job ID"] == "JOB-000001"
    assert second.iloc[0]["Persistence Status"] == "Previously Seen"


def test_strict_same_source_repost_within_60_days_reuses_canonical():
    _, registry = resolve_canonical_jobs(pd.DataFrame([make_job("linkedin:1")]), empty_registry())
    repost, _ = resolve_canonical_jobs(pd.DataFrame([make_job("linkedin:2", first_seen="2026-09-20", location="New York City, NY")]), registry)
    assert repost.iloc[0]["Job ID"] == "JOB-000001"
    assert repost.iloc[0]["Persistence Status"] == "Previously Seen"


def test_unambiguous_cross_source_historical_match_reuses_canonical():
    _, registry = resolve_canonical_jobs(pd.DataFrame([make_job("linkedin:1", source="LinkedIn")]), empty_registry())
    observation, _ = resolve_canonical_jobs(pd.DataFrame([make_job("indeed:99", first_seen="2026-09-20", source="Indeed")]), registry)
    assert observation.iloc[0]["Job ID"] == "JOB-000001"
    assert observation.iloc[0]["Persistence Status"] == "Previously Seen"
    assert observation.iloc[0]["Persistence Match Reason"] == "Conservative cross-source historical match"


def test_strict_repost_after_60_days_gets_new_canonical():
    _, registry = resolve_canonical_jobs(pd.DataFrame([make_job("linkedin:1", first_seen="2026-01-01")]), empty_registry())
    repost, _ = resolve_canonical_jobs(pd.DataFrame([make_job("linkedin:2", first_seen="2026-04-15")]), registry)
    assert repost.iloc[0]["Job ID"] == "JOB-000002"
    assert repost.iloc[0]["Persistence Status"] == "New"


def test_exact_remote_across_cities_retains_aliases_on_one_canonical_job():
    first = make_job("linkedin:1", location="New York, NY")
    first["Work Model"] = "Remote"
    _, registry = resolve_canonical_jobs(pd.DataFrame([first]), empty_registry())
    second = make_job("indeed:2", first_seen="2026-09-20", location="Austin, TX", source="Indeed")
    second["Work Model"] = "Remote"
    result, updated = resolve_canonical_jobs(pd.DataFrame([second]), registry)
    assert result.iloc[0]["Job ID"] == "JOB-000001"
    assert result.iloc[0]["Persistence Status"] == "Previously Seen"
    assert set(updated["vacancies"]["JOB-000001"]["source_aliases"]) == {"linkedin:1", "indeed:2"}


def test_different_remote_description_does_not_override_city_conflict():
    first = make_job("linkedin:1", location="New York, NY")
    first["Work Model"] = "Remote"
    _, registry = resolve_canonical_jobs(pd.DataFrame([first]), empty_registry())
    second = make_job("indeed:2", first_seen="2026-09-20", location="Austin, TX", source="Indeed")
    second["Work Model"] = "Remote"
    second["Job Description"] = "Own product roadmap and delivery."
    result, _ = resolve_canonical_jobs(pd.DataFrame([second]), registry)
    assert result.iloc[0]["Job ID"] == "JOB-000002"
