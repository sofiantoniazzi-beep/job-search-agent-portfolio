# Job Search Agent

**An AI-assisted system I designed and built to turn a broad, messy job search into a structured decision workflow — automatically discovering, evaluating, ranking, and tracking opportunities while keeping application decisions human-controlled.**

> **Portfolio version:** this repository is a clean-room, sanitized representation of my private production system. Personal candidate evidence, credentials, live spreadsheet IDs, cloud resource identifiers, retrieved job data, and other production configuration are excluded or replaced with synthetic examples.

## Why I built it

I wanted to solve a problem I was experiencing myself: job boards are good at surfacing vacancies, but much less useful for making consistent decisions across hundreds of imperfectly described opportunities.

The hard part was not simply finding more jobs. It was building a system that could answer, repeatedly and transparently:

- Is this actually a new opportunity, or the same vacancy reposted somewhere else?
- Is it compatible with my geographic and work constraints?
- How strong is the match based only on experience I can substantiate?
- Does the role fit the direction I want to move in, not just what I *could* do?
- Which CV positioning makes the most sense?
- Which opportunities deserve attention first?

What began as a personal workflow evolved into a production system that now runs unattended.

## What I built

The agent follows this decision flow:

**Discover → Normalize → Deduplicate → Resolve Identity → Filter → Assess → Route → Track → Rank → Maintain**

It currently:

- retrieves vacancies from LinkedIn, Indeed, and Himalayas;
- maintains persistent canonical vacancy identities across duplicates and reposts;
- combines deterministic rules with evidence-bounded LLM assessment;
- separates professional capability from career-direction fit;
- routes qualified jobs to the most appropriate CV strategy;
- maintains a Google Sheets Tracker, Ranker, and Run Log;
- tracks model usage and cost where providers expose exact accounting;
- uses recovery checkpoints and conservative state-commit rules for unattended execution;
- runs availability maintenance separately so liveness checks cannot corrupt discovery state.

The private production system has completed unattended end-to-end runs. This public repository recreates the substantive architecture with sanitized reference code, synthetic data, and **26 passing portfolio tests**.

## What made this interesting

This became much more than an automation script. Several product and system-design questions shaped the project:

**A job posting is not necessarily a job.** The same vacancy can appear on several platforms or be reposted under a new source ID, so I separated source observations from persistent canonical vacancy identity.

**Filter certainty; score ambiguity.** Deterministic rules handle conditions the system can establish confidently. Ambiguous professional fit is preserved for semantic assessment instead of being prematurely filtered out.

**LLMs should have bounded authority.** The model evaluates evidence and gaps, but Python owns score arithmetic, thresholds, recommendation logic, and validation. Candidate Evidence acts as a factual boundary against invented experience.

**Capability is not the same as career direction.** A role can be a strong skills match and still be the wrong next step, so career-direction fit is modeled separately.

**Failure behavior matters.** Canonical state advances only after the downstream human-facing workflow succeeds, and availability checks prefer an explicit Unknown state over falsely declaring a vacancy closed.

These decisions are explored in more detail in the [case study](docs/case-study.md), [matching methodology](docs/matching-methodology.md), and [production reliability notes](docs/production-reliability.md).

## See it quickly

The architecture and sanitized Google Sheets views below show the production workflow without exposing personal job-search data. If you want the deeper technical implementation, continue through this README or browse the [architecture documentation](docs/architecture.md).

If you want to use the methodology to build your own version, start with [AI_BUILD_GUIDE.md](AI_BUILD_GUIDE.md), which walks through **career discovery → MVP → productionization** using your own evidence and preferences.

## System architecture

![Job Search Agent architecture](assets/architecture.svg)

The production deployment runs daily discovery and weekly availability as separate scheduled cloud jobs. See [`docs/architecture.md`](docs/architecture.md) for the audited stage-by-stage design and architecture-to-code map.

## The operational interface is Google Sheets

The production system does **not** use a custom web application. Google Sheets is the human-facing operational layer: Python owns the automated workflow while the spreadsheet keeps review and application decisions inspectable and editable.

The images below are sanitized spreadsheet views with fictional vacancy/execution data. Their structures mirror the production worksheets without exposing private job-search data.

### Tracker — durable review workflow

![Sanitized Google Sheets Tracker view](assets/tracker_mockup.svg)

The production Tracker has **56 columns** spanning job metadata, assessment, CV routing, workflow, provenance and availability. The view above shows the first portion of that schema. New qualified canonical jobs append once; rediscovered jobs refresh automation-owned observation metadata when a Tracker row exists without overwriting user-managed fields such as Status or Notes.

### Ranker — derived attention queue

![Sanitized Google Sheets Ranker view](assets/ranker_mockup.svg)

The Ranker uses the production 13-column structure and narrows attention to active/reviewable jobs. Ranking Score combines **85% Base Match + 15% Freshness**; Domain Advantage is used as a tie-breaker rather than displayed as a Ranker column. Scheduled refreshes run directly from Python, while Apps Script is retained only for selected interactive spreadsheet behavior.

### Run Log — operational observability

![Sanitized Google Sheets Run Log view](assets/run_log_mockup.svg)

The Run Log records timestamps, status, duration, source retrieval counts, canonical/New/Previously Seen counts, Tracker activity, Ranker refresh, provider costs and error context. It is observational and best-effort rather than part of the canonical transaction.

## Matching: fit without CV hallucination

Instead of asking a model for a generic similarity score, the system decomposes Base Match into explicit dimensions:

| Dimension | Weight |
| --- | ---: |
| Responsibilities & Experience Fit | 45 |
| Skills & Capabilities Fit | 30 |
| Career-Direction Fit | 15 |
| Seniority Fit | 10 |
| **Base Match** | **100** |

**Domain Advantage (0–10)** is kept outside Base Match so relevant domain experience can improve ranking without making a new industry a penalty.

The assessment returns **Evidence**, **Gaps**, **Questions**, and a concise **Why**. Candidate Evidence acts as the factual boundary: the model may reason about overlap and transferability but may not invent experience. Python validates the payload and owns Base Match arithmetic, labels, application recommendations, and the career-direction safeguard.

A synthetic version of the assessment contract is available at [`prompts/expanded_semantic_assessment.example.txt`](prompts/expanded_semantic_assessment.example.txt). More detail is in [`docs/matching-methodology.md`](docs/matching-methodology.md).

## Identity and cost control

The system distinguishes a **source observation** from a **canonical vacancy**. Same-run duplicates are collapsed before persistence. Identical remote advertisements can share an identity across sources and city labels when normalized company, title, and full description match exactly. Other listings retain conservative city compatibility and description-similarity rules. Historical identity resolution then prioritizes known aliases, strict same-source repost matching, and one unambiguous conservative cross-source historical match before creating a new `JOB-######` identity. The registry retains all source aliases so rediscovery resolves to the same canonical vacancy.

Only **new canonical vacancies** enter the full decision engine and semantic assessment. Previously Seen vacancies update observation state without paying for the same full matching call again.

False merges are treated as more damaging than leaving an occasional duplicate separate.

## Reliability decisions

The production system was hardened around partial failure, not only the happy path:

- canonical registry state advances only after successful Tracker synchronization and Ranker refresh;
- run IDs and checkpoints support recovery without unnecessarily repeating expensive stages;
- resumed runs verify the registry state they started from before they may continue;
- failed runs can preserve recovery state without advancing canonical state;
- deterministic gates precede semantic model calls;
- exact provider usage/cost is recorded where the provider exposes sufficient accounting;
- weekly availability is a separate maintenance workflow and never advances canonical discovery state;
- availability prefers `Unknown` to a destructive false `Closed` classification;
- absence from finite retrieval is **never** treated as closure evidence.

The unattended daily production workflow has been validated end-to-end, and the operational Tracker uses a **56-column schema**.

See [`docs/production-reliability.md`](docs/production-reliability.md).

## Build your own

The repository is intentionally reusable without pretending the private implementation is a generalized product. [`AI_BUILD_GUIDE.md`](AI_BUILD_GUIDE.md) instructs an AI assistant to derive a new user's configuration rather than copy the reference candidate.

The replication path is:

1. [`Phase 0 — Career Discovery & Candidate Modeling`](docs/phase-0-discovery.md)
2. [`Phase 1 — Build the MVP`](docs/phase-1-mvp.md)
3. [`Phase 2 — Productionize the Agent`](docs/phase-2-production.md)

The semantic geographic eligibility step in Phase 1 is optional for a local-only search whose deterministic location rules already establish eligibility. It is useful for remote postings with nuanced residency or hiring restrictions.

Synthetic templates for Candidate Evidence, career preferences, role taxonomy, CV variants and search profiles live under `templates/`.

## Portfolio code

The `src/` directory mirrors the substantive production architecture with sanitized reference counterparts: retrieval, normalization, deterministic and geographic eligibility, same-run deduplication, historical canonical persistence, expanded semantic assessment, CV routing, Tracker synchronization, Ranker logic, checkpoints, run logging, cloud-state boundaries, conservative availability maintenance, and daily-vs-weekly orchestration.

These are reference implementations, not a drop-in copy of the private deployed repository.

## Technology

**Python 3.12 · pandas · JobSpy · Anthropic · Mistral · OpenAI · Google Sheets / gspread · Google Cloud Storage · Cloud Run Jobs · Cloud Scheduler · Google Apps Script**

## Repository map

```text
.
├── AI_BUILD_GUIDE.md              # AI-assisted replication entrypoint
├── assets/                        # architecture + sanitized Sheets views
├── config/                        # sanitized configuration examples
├── docs/
│   ├── phase-0-discovery.md       # derive the candidate model
│   ├── phase-1-mvp.md             # build the first working agent
│   ├── phase-2-production.md      # productionize it
│   ├── architecture.md
│   ├── case-study.md
│   ├── matching-methodology.md
│   ├── production-reliability.md
│   └── portfolio-sanitization.md
├── templates/                     # reusable Phase 0 configuration structures
├── prompts/                       # synthetic semantic-assessment contract
├── src/                           # sanitized reference implementation
├── tests/                         # portfolio reference tests
├── .env.example
└── requirements.txt
```

## Running the portfolio tests

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q
```

The **26 reference tests** cover matching thresholds, career-direction safeguards, model-output validation, source-aware availability semantics, canonical availability aggregation, cross-source deduplication, exact remote identity, historical canonical persistence and repost handling, CV routing, Tracker semantics, Ranker behavior, daily orchestration, weekly maintenance, and daily-vs-weekly state-commit boundaries.

## Privacy and sanitization

This repository was created independently rather than by making the production repository public. That prevents private Candidate Evidence and production configuration from surviving in inherited Git history. Replicating users should keep their own Candidate Evidence and live configuration private as well. See [`docs/portfolio-sanitization.md`](docs/portfolio-sanitization.md).

## Status

The portfolio architecture, AI-assisted replication framework, Phase 0 → Phase 1 → Phase 2 narrative, sanitized Google Sheets operational visuals, test suite, and public-release audit are complete. The repository is ready for public release.
