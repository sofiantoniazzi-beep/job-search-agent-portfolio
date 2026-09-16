# Phase 0 — Career Discovery & Candidate Modeling

## Goal

Before automating job search, build a structured model of the person the system is searching for. This phase converts professional history, career ambitions, constraints, and positioning choices into approved configuration that later stages can use without inventing evidence.

## 0.1 Professional experience discovery

Do not rely only on an existing CV. Interview the user role by role and project by project.

For each meaningful project or responsibility, capture:
- context and problem;
- scope;
- the user's specific role;
- responsibilities and ownership;
- stakeholders and collaborators;
- methods and tools;
- decisions the user influenced or owned;
- deliverables;
- measurable results where genuinely known;
- reusable capabilities demonstrated;
- domains / industries involved.

Ask follow-up questions when an answer is vague. Do not manufacture metrics or infer ownership the user has not claimed.

### Output

Create a private Candidate Evidence artifact using `templates/candidate-evidence.example.json` as a structural reference.

The evidence should be richer than a CV. A CV is a selected presentation; Candidate Evidence is the factual source from which later matching and CV variants are derived.

## 0.2 Career-direction discovery

Separate **what the user can do** from **what the user wants to do next**.

Explore:
- activities that create energy or interest;
- activities the user wants more of;
- activities they can perform but want less of;
- preferred degree of ownership;
- client / stakeholder interaction preferences;
- analytical vs operational vs strategic work;
- individual vs cross-functional work;
- mission/domain preferences;
- learning/growth priorities;
- work environment constraints.

Record both positive and negative signals. These later inform Career Direction scoring rather than becoming unsupported assumptions about professional capability.

### Output

Create `career-preferences.json` from the example template.

## 0.3 Role exploration and taxonomy

Explore broadly before narrowing retrieval.

Build a list of possible roles and classify them as:
- **YES** — actively interested;
- **MAYBE** — plausible/adjacent, requires evaluation;
- **NO** — intentionally excluded.

For YES and MAYBE roles, identify:
- role family;
- common title variants;
- transferable evidence supporting the role;
- likely gaps;
- domain specializations;
- search keywords;
- titles that look similar but represent unwanted work.

Do not assume a role is desirable merely because the candidate is qualified for it.

### Output

Create `role-taxonomy.json` from the example template. This becomes an input to retrieval profiles, deterministic gates, semantic assessment, and CV routing.

## 0.4 Base CV strategy

Instead of tailoring a CV from scratch for every vacancy, define a manageable set of evidence-grounded base representations.

Ask:
- Which role families require materially different positioning?
- Which specializations within a function justify a distinct version?
- Which experience should be emphasized for each variant?
- Which facts must remain identical across variants?
- Which languages/localizations are needed?

Use the principle **function first, specialization second** when it matches the user's strategy. The number and names of CV variants are user-specific; do not copy the reference project's seven variants by default.

### Output

Create `cv-variants.json` describing each variant, target function, optional specialization, language, and positioning intent.

## 0.5 Geography, authorization, and localization

Capture only what is necessary for job eligibility:
- residence / intended residence;
- target countries or regions;
- work authorizations relevant to the search;
- acceptable local/hybrid cities;
- remote-work constraints;
- material timezone constraints;
- CV / application languages.

Keep this private. Public repositories should contain fictional examples only.

## 0.6 Search profiles

Convert the approved taxonomy into retrieval profiles. Search broadly enough to capture adjacent opportunities without treating search keywords as final fit judgments.

A profile can include:
- role family;
- query/title terms;
- geography;
- remote/local intent;
- source;
- lookback window;
- discovery-only adjacent keywords.

Search is a recall mechanism. Eligibility and matching happen downstream.

## Phase 0 review checkpoint

Before Phase 1, present the user with a compact summary of:
1. Candidate Evidence coverage;
2. desired/undesired career characteristics;
3. YES/MAYBE/NO role taxonomy;
4. role families and search profiles;
5. CV variant strategy;
6. geography and localization rules.

Ask the user to correct omissions or misinterpretations. Only approved outputs should become system configuration.

## Why this phase matters

The quality of the automation is bounded by the quality of its candidate model. Phase 0 prevents the system from treating an old CV as the complete truth, confusing capability with preference, or embedding arbitrary role/search assumptions directly in code.
