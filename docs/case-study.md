# Case Study — Job Search Agent

## The problem began before automation

The first challenge was not finding job postings. It was defining what the search should optimize for.

After roughly six years of professional experience, an existing CV was too compressed to act as a complete model of demonstrated capability, and job titles alone were too crude to describe the next career move. A useful system needed to understand both **what evidence exists** and **what kind of work the candidate actually wants next**.

The project therefore evolved through three phases rather than beginning as a production automation project.

## Phase 0 — Career Discovery & Candidate Modeling

The project started with an exhaustive reconstruction of professional experience rather than CV editing. Major projects were decomposed into problem, scope, role, responsibilities, stakeholders, methods/tools, decisions, deliverables, results, and reusable capabilities.

That produced a richer **Candidate Evidence** boundary: a factual source for later matching that was deliberately broader than any single CV.

Career-direction discovery then separated **capability from career fit**. Work characteristics the candidate wanted more of — such as strategy, problem-solving, ownership, client interaction and cross-functional work — were modeled separately from activities the candidate could perform but did not want to optimize a search around.

A broad role exploration classified roles into YES / MAYBE / NO and grouped viable paths into role families, adjacent titles and retrieval keywords. Finally, that taxonomy was translated into seven base CV positioning strategies in the private implementation, with localized versions where required.

Phase 0 established the inputs that later became software concepts:

| Discovery output | System implementation |
| --- | --- |
| Project-level professional evidence | Candidate Evidence factual boundary |
| Desired / undesired work | Career Direction assessment |
| YES / MAYBE / NO role exploration | Role families, taxonomy, retrieval keywords and gates |
| Transferable capabilities | Responsibilities & Skills assessment |
| Base positioning strategies | CV variants |
| Function vs specialization choices | CV routing |
| Geography and language requirements | Retrieval, eligibility and localization rules |

The key product insight was that the system should not merely ask **“Is this candidate qualified?”** It should also ask **“Is this opportunity aligned with the direction they chose, and which truthful representation of their experience best fits it?”**

## Phase 1 — MVP: automate the decision workflow

Once the candidate model existed, the next question was whether the repetitive search and evaluation workflow could be automated usefully.

The MVP connected vacancy retrieval to normalization, high-confidence eligibility filtering, evidence-bounded semantic fit assessment, CV routing, and a Google Sheets review workflow.

Broad retrieval was intentional. Search keywords were treated as discovery mechanisms rather than final fit judgments. Deterministic rules handled clear exclusions; ambiguous roles continued to semantic assessment.

Instead of asking an LLM for an opaque similarity score, matching was decomposed into Responsibilities, Skills, Career Direction and Seniority. Domain Advantage remained outside the 100-point Base Match so prior industry experience could help without penalizing a move into a new domain.

The output landed in a Google Sheets **Tracker** for durable human review and a derived **Ranker** that combined fit with freshness. Application submission remained a human decision.

Phase 1 proved the decision model. It also exposed the limitations of a stateless pipeline: duplicate source listings, reposts, repeated model spend, partial-write risks, and stale vacancy maintenance.

## Phase 2 — Productionization: make it safe to run unattended

Phase 2 reframed the project from “automated matching” into a stateful production system.

### Canonical vacancy identity

A source posting became an observation rather than the durable job itself. Same-run duplicates and qualifying historical observations resolve conservatively to stable `JOB-######` identities while retaining source aliases and provenance.

This solved both workflow duplication and cost: only **new canonical vacancies** enter full semantic assessment.

### Transaction-safe workflow state

Canonical state advances only after Tracker synchronization and Ranker refresh succeed. That prevents a downstream failure from causing a future run to believe a vacancy was already delivered when it was not.

Tracker automation preserves user-managed fields such as Status and Notes. Retrieval state and human application state remain separate.

### Recovery and cost control

Run IDs and checkpoints allow interrupted executions to resume without unnecessarily repeating expensive stages. Recovery state is separated from canonical state, and resumed runs verify the registry state they started from before they can commit.

Deterministic gates precede LLM calls, semantic stages use separate caches where useful, and exact provider usage/cost is recorded when available.

### Conservative availability maintenance

Availability became a separate weekly workflow. It may update availability fields and refresh the Ranker, but it does not discover jobs, create canonical IDs, rerun matching, route CVs, mutate the registry, or update Last Seen.

Closure is deliberately conservative: **Unknown is safer than a false Closed**. Absence from finite retrieval is never closure evidence, and multiple source observations aggregate so one dead duplicate cannot close a vacancy still active elsewhere.

## Production outcome

By Phase 2 closure, the private production system had retained more than **7,600 canonical vacancies**, used a **56-column Google Sheets Tracker**, supported controlled recovery/resume, separated weekly availability maintenance from daily discovery, and completed an unattended daily end-to-end execution successfully.

The most important outcome, however, is architectural: a qualitative career-discovery process became a structured, inspectable decision system while keeping factual evidence and final application decisions under human control.

## What was difficult

The retrieval adapters were not the hardest part. The difficult decisions were methodological and stateful:

- deciding what the system was allowed to infer about a candidate;
- separating capability from career preference;
- deciding when two postings represented the same real vacancy;
- preventing canonical state from advancing after partial failure;
- deciding what evidence was strong enough to close a vacancy;
- separating automation-owned fields from user-owned workflow state;
- deciding where semantic models added enough value to justify cost.

These required product judgment as much as implementation.

## What this project demonstrates

The project spans problem discovery, professional-evidence modeling, taxonomy and methodology design, product workflow design, LLM guardrails, data normalization, identity resolution, state management, recovery logic, cost control, Google Sheets operational UX, testing, and cloud deployment.

The public portfolio repository is a clean-room sanitized reference implementation. It also documents the Phase 0 → Phase 1 → Phase 2 methodology so another candidate can derive their own configuration rather than copying the original candidate's private evidence or career choices.
