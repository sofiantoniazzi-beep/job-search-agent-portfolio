"""Sanitized deterministic CV routing.

The production project maintains a larger private set of base CVs. This portfolio
version demonstrates the same routing principle: function first, specialization
second, with one clearly selected base CV per surfaced vacancy.
"""

from __future__ import annotations

import re

PRODUCT_GENERAL = "Product Manager - General"
PRODUCT_TECH_AI = "Product Manager - Technical & AI"
PRODUCT_SPECIALIST = "Product Specialist - General"
CONSULTING_GENERAL = "Consulting & Strategy - General"
AI_CONSULTING = "Consulting & Strategy - AI Consulting"


def _text(job: dict) -> str:
    return " | ".join(
        str(job.get(field, "") or "").lower()
        for field in ("Job Title", "Job Description", "Role Family", "Domain Signals")
    )


def route_cv(job: dict) -> dict:
    title = str(job.get("Job Title", "") or "").lower()
    role_family = str(job.get("Role Family", "") or "").lower()
    text = _text(job)

    ai_signal = bool(re.search(r"\b(ai|artificial intelligence|machine learning|genai|llm)\b", text))
    specialist_signal = bool(re.search(r"\b(product specialist|solutions consultant|pre-sales|enablement)\b", title))
    product_signal = "product" in role_family or bool(re.search(r"\bproduct manager\b", title))
    strategy_signal = "strategy" in role_family or "consult" in role_family or bool(
        re.search(r"\b(strategy|consultant|transformation)\b", title)
    )

    if specialist_signal:
        variant = PRODUCT_SPECIALIST
        reason = "Product / solutions specialist function is primary."
    elif product_signal and ai_signal:
        variant = PRODUCT_TECH_AI
        reason = "Product role with clear AI / technical specialization."
    elif product_signal:
        variant = PRODUCT_GENERAL
        reason = "General product-management function."
    elif strategy_signal and ai_signal:
        variant = AI_CONSULTING
        reason = "Strategy / consulting role substantively centered on AI."
    else:
        variant = CONSULTING_GENERAL
        reason = "Broad strategy / consulting fallback."

    return {"CV Variant": variant, "CV Language": "English", "CV Routing Reason": reason}


def route_jobs(jobs: list[dict]) -> list[dict]:
    routed: list[dict] = []
    for job in jobs:
        output = dict(job)
        output.update(route_cv(job))
        routed.append(output)
    return routed
