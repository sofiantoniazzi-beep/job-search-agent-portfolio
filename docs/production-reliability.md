# Production Reliability & Cost Control

## Reliability goals

The productionization phase focused on making the system safe to run unattended rather than merely making the happy path work. The main concerns were duplicate identity, partial writes, recovery after failure, conservative availability classification, and controlling repeated LLM spend.

## Transaction boundary

The canonical vacancy registry is persisted only after successful Tracker synchronization **and Ranker refresh**. If a run fails before that point, durable vacancy state does not falsely indicate that downstream processing completed.

This creates an explicit transaction-like boundary across systems that do not share a database transaction.

## Checkpoint and recovery

Runs receive unique IDs and write checkpoint state as major stages complete. Recovery can resume the same run rather than starting a new discovery/matching cycle. This is especially important after expensive semantic assessment or successful Tracker writes.

The recovery path was validated by deliberately resuming a failed production execution from its existing checkpoint and completing the remaining downstream stages.

## Run logging

The operational Run Log records execution metadata including:

- run ID and execution mode;
- start/end timing and status;
- source retrieval counts;
- job-processing counts;
- Tracker synchronization results;
- provider token/cost metrics where exact usage is available;
- failure information; and
- recovery metadata.

Failed runs are logged as first-class outcomes rather than disappearing behind an exception.

## LLM cost controls

The canonical registry acts as a cost-control layer as well as an identity layer. Semantic matching is performed only for **new canonical vacancies**. Previously seen jobs can update observation metadata without being rescored every day.

Exact Mistral token usage and run cost are captured from provider usage data. Combined provider totals are not estimated when exact usage is unavailable; unknown cost remains unknown rather than being fabricated.

## Availability safety

The weekly availability workflow deliberately favors Unknown over false Closed classifications.

Closed requires affirmative evidence such as explicit closure/unavailability text or expiry metadata. The following are not sufficient closure evidence on their own:

- absence from finite retrieval;
- HTTP 404/410 without reliable job-state evidence;
- authentication/login/checkpoint pages;
- throttling or server errors;
- a recognizable job page that lacks a clear Apply control but provides no explicit closure evidence.

This policy protects the application workflow from destructive false negatives.

## Validation performed

Production hardening included deterministic local tests, a controlled manual cloud execution, a forced recovery/resume path, an unattended scheduled daily execution, downstream Tracker/Ranker verification, and a separate cloud validation of the weekly availability workflow.

At Phase 2 closure the production canonical registry contained more than 7,600 vacancies with zero duplicate alias ownership after audit. The operational Tracker schema contained 56 columns spanning source metadata, assessment output, workflow fields, and availability state.

## Remaining observability opportunities

Additional retrieval-health observability and Scheduler-specific log alerting are useful future enhancements, but were intentionally separated from the Phase 2 completion criteria after the core execution, recovery, state, and downstream workflows were validated.
