# AI Build Guide

This repository can be used as an AI-assisted blueprint for building a personal Job Search Agent.

## Instructions for the AI assistant

You are helping a user build **their own** system from this reference architecture. Do not copy the fictional example candidate or infer that the original candidate's preferences, geography, scoring choices, CV variants, or exclusions apply to the new user.

Work sequentially through Phase 0, Phase 1, and Phase 2. Ask focused questions, preserve user-approved decisions as structured configuration, and do not advance past a phase checkpoint until the user has reviewed its outputs.

Core rules:

1. Treat the user's statements and approved artifacts as the factual boundary. Never invent professional evidence.
2. Distinguish **capability** from **career direction**. A user can be qualified for work they do not want.
3. Derive retrieval keywords, eligibility rules, scoring configuration, and CV routing from the user's Phase 0 outputs.
4. Prefer deterministic logic for hard rules, arithmetic, identity, state transitions, and validation. Use LLM judgment only where semantic interpretation is genuinely useful.
5. Preserve human control over application decisions. The reference architecture discovers, assesses, routes, ranks, and tracks; it does not require automatic application submission.
6. Build the simplest working MVP before adding production reliability infrastructure.
7. When adapting reference code, replace example configuration rather than editing logic to encode personal facts.

## Start here

Read and follow these guides in order:

1. [`docs/phase-0-discovery.md`](docs/phase-0-discovery.md) — derive Candidate Evidence, career preferences, role taxonomy, CV strategy, geography, and languages.
2. [`docs/phase-1-mvp.md`](docs/phase-1-mvp.md) — build retrieval, normalization, eligibility, semantic assessment, CV routing, Tracker, and Ranker.
3. [`docs/phase-2-production.md`](docs/phase-2-production.md) — add canonical identity, persistence, deduplication, caching, recovery, availability maintenance, logging, cost controls, and unattended cloud execution.

Use [`docs/architecture.md`](docs/architecture.md) as the final architecture reference and the files in `src/` as sanitized implementation examples.

## Phase checkpoints

### Phase 0 complete when

The user has explicitly reviewed and approved:
- structured Candidate Evidence;
- desired and undesired work characteristics;
- target role families and role taxonomy;
- base CV variants and routing intent;
- target geography / work authorization constraints;
- language and localization requirements;
- initial search profiles.

Do **not** begin scoring design from an existing CV alone if richer professional evidence can be elicited from the user.

### Phase 1 complete when

A local/manual run can retrieve jobs, normalize them, apply high-confidence eligibility rules, assess fit against approved evidence, select a CV representation, and write qualified opportunities into a human-review workflow. The user should be able to inspect why a job received its result.

### Phase 2 complete when

The system can run unattended without silently corrupting identity or workflow state; interrupted runs can recover safely; repeated observations do not repeatedly incur semantic assessment cost; availability maintenance is separated from discovery; and the user has validated an end-to-end scheduled run.

## Recommended interaction pattern

At the start of each phase:
- explain the goal in a few sentences;
- identify the artifacts that will be produced;
- work through one logical section at a time;
- summarize decisions before writing configuration;
- ask the user to approve or correct the summary;
- only then proceed.

If the user already has an artifact (CV, LinkedIn profile, role list, spreadsheet, existing code), use it as input, but verify whether it is complete enough for the current phase rather than assuming it is authoritative.

## Reference vs configuration

The repository intentionally separates reusable architecture from candidate-specific configuration. Files under `config/` and `templates/` are examples. A replicating user should create their own private configuration and keep sensitive evidence, credentials, spreadsheet IDs, cloud resource identifiers, and retrieved job data out of a public repository.
