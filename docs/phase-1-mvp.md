# Phase 1 — Build the MVP

## Goal

Turn the approved Phase 0 candidate model into a working local/manual decision workflow. The MVP should prove that broad retrieval can become explainable, evidence-bounded job recommendations before investing in production infrastructure.

## 1. Freeze Phase 0 inputs

Create private working versions of:
- Candidate Evidence;
- career preferences;
- role taxonomy;
- CV variants;
- geography/authorization configuration;
- search profiles.

Keep personal evidence and credentials outside a public repository.

## 2. Retrieval

Implement one source first, then add others. The reference project uses LinkedIn and Indeed through JobSpy plus Himalayas through its public jobs API, but a replicating user can choose sources appropriate to their market.

Retrieval should optimize for recall. Preserve provenance such as source listing ID, source, search query, URLs, posting date, location, work model, and raw description.

Do not make search keywords responsible for final fit decisions.

## 3. Normalization

Create one internal job schema. Normalize source-specific records without inventing missing information.

Typical fields include company, title, description, location, work model, source, source ID, URLs, posting date, salary metadata, employment type, and ingestion timestamp.

Normalization is a data boundary, not a matching stage.

## 4. Deterministic eligibility

Translate Phase 0's high-confidence exclusions into deterministic rules. Follow **filter certainty; score ambiguity**.

Good hard filters are explicit incompatibilities: for example, an internship when the user excludes internships or a clearly incompatible location requirement. Ambiguous seniority, adjacent functions, and uncertain fit should usually continue to scoring.

Use `src/eligibility.py` as a reference contract rather than copying its example flags blindly.

## 5. Geographic eligibility

Keep geography separate from professional fit. Ask only whether the role can be performed under the user's approved residence/work setup.

A semantic geography step can be useful when postings express restrictions in natural language. The model should not assess skills, seniority, desirability, or compensation in this step. Ambiguity should pass unless the user intentionally chooses a stricter policy.

**Optional for local-only searches:** If you are not searching for remote jobs and your deterministic filters already restrict postings to eligible local locations, you can skip the semantic geographic eligibility check. Keep the explicit local location and work-authorization rules; the semantic step is most useful for interpreting nuanced remote residency, hiring, payroll, and timezone restrictions.

See `src/geographic_eligibility.py`.

## 6. Matching design

Define explicit dimensions instead of asking an LLM for an unexplained overall fit score.

The reference implementation uses:
- Responsibilities & Experience Fit — 45;
- Skills & Capabilities Fit — 30;
- Career Direction Fit — 15;
- Seniority Fit — 10;
- Domain Advantage — separate 0–10 bonus/tie-break signal.

These weights are a reference design, not a universal requirement. If the user changes them, document why and keep arithmetic deterministic.

The semantic model should be constrained by Candidate Evidence. It may identify overlap, gaps, and questions; it must not invent candidate experience.

Python/code should validate score bounds and own arithmetic, labels, and workflow thresholds. See `src/matching.py`, `src/expanded_assessment.py`, and the synthetic prompt example.

## 7. Career-direction safeguard

A high capability score should not automatically create a high-priority recommendation when the role conflicts with the user's approved career direction.

Implement an explicit safeguard or equivalent rule derived from the user's preferences. Keep it transparent and code-owned.

## 8. CV routing

Route qualified jobs to the best approved base CV representation.

Prefer function before specialization when appropriate. A job mentioning AI should not automatically receive an AI CV if the underlying function is unrelated. A sustainability term should not override a clearly different role function.

Use `src/cv_routing.py` as a reference for the concept; derive actual variants and signals from Phase 0.

## 9. Human review workflow

Create a Google Sheets Tracker (or equivalent user-controlled interface) where qualified jobs can be reviewed.

At minimum, preserve:
- canonical/source identifier during the MVP;
- company/title/link;
- assessment and Base Match;
- application recommendation;
- Why / Evidence / Gaps / Questions;
- CV Variant;
- status and notes;
- source/provenance;
- first/last observation timestamps.

Keep human-managed fields separate from automation-owned fields.

Create a Ranker as a derived view of active opportunities. The reference uses 70% Base Match + 30% freshness with Domain Advantage as a tie-breaker; treat this as a configurable example.

## 10. Manual validation

Run the MVP against real postings and review false positives/negatives with the user.

Ask:
- Are obviously irrelevant jobs filtered?
- Are adjacent but interesting jobs surviving?
- Does the assessment cite real candidate evidence?
- Does Career Direction distinguish ability from desire?
- Does CV routing select the intended representation?
- Are explanations useful enough to challenge a score?
- Is the Tracker manageable as a daily workflow?

Adjust configuration before adding production complexity.

## Phase 1 checkpoint

Phase 1 is complete when a local/manual execution can:

`Retrieve → Normalize → Filter → Assess → Route → Track → Rank`

and the user has reviewed enough real results to trust the decision model as a useful assistant rather than an opaque classifier.

At this stage, duplicate/repost handling may still be simple. Phase 2 turns the MVP into a durable stateful system.
