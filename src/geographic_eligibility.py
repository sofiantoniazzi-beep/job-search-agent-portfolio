"""Portfolio-safe geographic eligibility prompt builder.

Candidate-specific facts are loaded from configuration rather than embedded in source code.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_candidate_config(path: str = "config/candidate.example.json") -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_system_prompt(candidate: dict[str, Any]) -> str:
    residence = candidate["residence_country"]
    authorizations = ", ".join(candidate.get("work_authorizations", []))
    cities = ", ".join(candidate.get("allowed_local_cities", []))

    return f"""You are evaluating GEOGRAPHIC ELIGIBILITY ONLY for a job-search system.

Candidate configuration:
- Residence country: {residence}
- Work authorizations: {authorizations}
- Allowed local/hybrid cities: {cities}

Determine whether the posting explicitly prevents the candidate from performing the role under this geographic setup.

Rules:
- Assess geography only, not job fit, skills, seniority, or compensation.
- Work authorization alone does not override explicit residency, payroll, hiring-country, or physical-location restrictions.
- Do not infer restrictions from company or office location unless the posting makes them requirements.
- Ambiguous or silent geography should PASS.
- FAIL only with explicit incompatible geographic evidence.

Return JSON only:
{{"eligibility": "PASS" or "FAIL", "reason": ""}}

PASS requires an empty reason. FAIL requires a concise explicit geographic reason."""


def build_job_prompt(job: dict[str, Any]) -> str:
    fields = ["Job Title", "Company", "Location", "Work Model", "Remote Restrictions", "Job Description"]
    payload = {field: str(job.get(field, "") or "").strip() for field in fields}
    return "Assess the following job for geographic eligibility.\n\n" + json.dumps(
        payload, ensure_ascii=False, indent=2
    )
