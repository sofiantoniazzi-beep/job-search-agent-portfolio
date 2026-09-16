# Phase 2 — Productionize the Agent

## Goal

Turn the validated MVP into a stateful system that can run unattended without repeatedly evaluating the same vacancy, corrupting workflow state, or treating temporary failures as truth.

Productionization is primarily about **identity, transactions, recovery, observability, and failure semantics**.

## 2.1 Canonical vacancy identity

A source listing ID identifies a provider observation, not necessarily a unique real-world vacancy. Introduce stable canonical IDs such as `JOB-######` and preserve provider aliases behind each canonical vacancy.

Use two identity layers:
- same-run deduplication for high-confidence duplicate observations retrieved together;
- historical persistence for aliases, reposts, and cross-source observations seen on different runs.

Resolve historical identity conservatively: known alias → strict same-source repost → one unambiguous cross-source historical match → new canonical vacancy. If identity is ambiguous, keeping two records is safer than a destructive false merge.

See `src/deduplicate.py` and `src/persistence.py`.

## 2.2 Assess only new canonical vacancies

Split observations after persistence into **New** and **Previously Seen**. Only New canonical vacancies should enter expensive professional-fit assessment and CV routing.

Previously Seen jobs can refresh observation metadata without paying for the same semantic judgment again. This makes identity resolution part of the cost-control architecture, not merely data cleanup.

## 2.3 Separate canonical state from workflow state

Canonical persistence answers: *Have we seen this real vacancy before, and through which source observations?*

The Tracker answers: *What is the user's current review/application state for a qualified vacancy?*

Do not conflate them. A canonical vacancy may legitimately never enter the Tracker because it failed qualification on its first observation.

Automation must not overwrite human-managed fields such as Notes or workflow Status when a vacancy is rediscovered.

## 2.4 Make spreadsheet writes idempotent

Use canonical Job ID as the Tracker idempotency key. New qualified jobs append once; Previously Seen jobs update only automation-owned observation fields if a Tracker row exists.

For remote APIs, design for ambiguous write failures: if an append times out after the server may have accepted it, reread IDs before retrying rather than blindly appending again.

The Ranker should be a derived view refreshed after Tracker synchronization. Preserve spreadsheet formatting and interactive behavior when replacing values.

See `src/tracker_writer.py`, `src/application_workflow.py`, and `src/ranker_refresh.py`.

## 2.5 Define the state-commit boundary

Do not advance canonical vacancy state merely because retrieval and matching succeeded.

The reference transaction is:

`Process → Tracker sync → Ranker refresh → Commit canonical state`

If Tracker synchronization or Ranker refresh fails, canonical state must not advance. Otherwise a future run could classify jobs as Previously Seen even though they never reached the human workflow.

See `src/pipeline.py`.

## 2.6 Add caches and cost controls

Put deterministic gates before semantic calls. Cache semantic geography and full matching separately when they have different costs/failure boundaries.

Use stable checkpoint/cache keys based on source identity and relevant versioning. Version caches when prompt contracts or decision logic materially change.

Where providers expose reliable token/usage accounting, record actual usage rather than estimating from successful parsed outputs only. Billable responses that later fail validation can still cost money.

## 2.7 Add run IDs and recovery checkpoints

Give each daily execution a unique run ID. Persist run-specific checkpoints separately from canonical state so an interrupted run can resume without repeating completed expensive stages.

Protect against stale recovery: record the canonical registry hash/base version associated with the run and refuse to let an old checkpoint overwrite newer canonical truth.

Recovery artifacts may advance after a failed run; canonical state may not.

See `src/run_checkpoint.py`, `src/cloud_state.py`, and `src/cloud_runner.py`.

## 2.8 Add operational logging

Create a Run Log that records useful operational facts such as:
- start/completion time and duration;
- source retrieval counts;
- canonical/New/Previously Seen counts;
- Tracker writes;
- Ranker refresh result;
- provider cost where known;
- final status and error context.

Logging should help diagnose the system without becoming part of the canonical transaction. A logging failure should not normally invalidate an otherwise successful operational run.

## 2.9 Separate availability maintenance from discovery

Do not use the daily discovery pipeline to repeatedly recheck old vacancies.

Create a separate periodic availability workflow over the active Tracker backlog. It should not discover new canonical vacancies, run semantic matching, route CVs, mutate the vacancy registry, or update Last Seen.

Availability should use conservative source-specific evidence and three states:
- **Active**;
- **Closed**;
- **Unknown**.

Canonical aggregation: any represented source Active → Active; all represented sources Closed → Closed; otherwise Unknown.

Absence from a finite retrieval pool is not closure evidence. Temporary errors, authentication walls, throttling, and ambiguous pages should generally become Unknown. Source-specific affirmative closure evidence can be stronger where justified.

See `src/availability.py` and `src/weekly_availability.py`.

## 2.10 Containerize and schedule

Once local production behavior is stable:
- containerize the runtime;
- externalize credentials and environment-specific IDs;
- store canonical/recovery state in durable object storage;
- create separate scheduled jobs for daily discovery and periodic availability;
- keep the same tested Python entrypoints locally and in the cloud where practical.

The reference production deployment uses Docker, Cloud Run Jobs, Cloud Scheduler, Cloud Storage, and Google Sheets. These are implementation choices, not requirements of the architecture.

## 2.11 Validate unattended execution

Before calling the system production-ready, run it without manual intervention and verify the complete transaction:

`Scheduled start → state restore → retrieval → identity → New-only decision engine → Tracker → Ranker → canonical commit → operational log`

Also validate failure/recovery paths and the separate availability workflow.

## Phase 2 checkpoint

Phase 2 is complete when:
- canonical identity survives duplicates and reposts conservatively;
- repeated observations do not trigger repeated full semantic assessment;
- human workflow state is protected;
- downstream failures do not incorrectly advance canonical state;
- interrupted runs can recover safely;
- availability cannot easily create destructive false closures;
- costs and run outcomes are observable;
- daily and maintenance workflows are separated;
- at least one unattended end-to-end run has been reviewed successfully.

The goal is not merely automation. It is **automation whose failure modes are explicit and recoverable**.
