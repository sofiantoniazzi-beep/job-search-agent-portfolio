# Matching Methodology

## Objective

The matching layer is designed to answer a narrower question than keyword similarity: **Is this a good opportunity for this candidate, based only on evidence the system is allowed to use?**

The system therefore separates functional fit, career preference, seniority, and domain context rather than asking one model for an opaque overall score.

## Base Match — 100 points

| Component | Weight | Purpose |
| --- | ---: | --- |
| Responsibilities & Experience Fit | 45 | Similarity between the substantive work and demonstrated/transferable experience |
| Skills & Capabilities Fit | 30 | Required capabilities, tools, methods, and professional knowledge |
| Career-Direction Fit | 15 | Alignment between likely day-to-day work and the candidate's desired work characteristics |
| Seniority Fit | 10 | Organizational level, autonomy, scope, authority, and leadership expectations |

`Base Match = Responsibilities + Skills + Career Direction + Seniority`

## Domain Advantage — separate 0–10 signal

Domain Advantage captures contextual benefit from relevant industry/domain experience without penalizing candidates for entering a new industry and without double-counting functional fit. It is kept outside the 100-point Base Match and is used as an additional ranking signal.

## Decision bands

| Base Match | Assessment | Application |
| ---: | --- | --- |
| 90–100 | Exceptional | Priority Apply |
| 80–89 | Very Strong | Priority Apply |
| 75–79 | Strong | Apply |
| 65–74 | Possible | Consider |
| <65 | Weak | Skip |

A low Career-Direction score constrains the application recommendation even when the candidate could technically perform the job. This prevents high capability fit from promoting work that conflicts with the candidate's stated direction.

## Evidence boundary

Candidate Evidence is an authoritative factual boundary. Each capability includes evidence strength and, where necessary, explicit guardrails such as "do not infer people management" or "analytical Python use only; do not infer software engineering."

The model is instructed to distinguish between:

- direct evidence;
- strongly transferable evidence;
- partially transferable or learnable gaps;
- material gaps; and
- no evidence.

This design addresses a common LLM failure mode in career matching: converting plausible transferability into fabricated experience.

## Structured output

Each assessment returns component scores plus:

- up to three synthesized strengths (`Evidence`);
- up to three material `Gaps`;
- `Questions` only when uncertainty could materially change the decision; and
- a concise `Why` synthesis.

The scoring output is validated programmatically, including the arithmetic relationship between component scores and Base Match.

## Wildcard discovery

Role taxonomy is used for retrieval and routing, but it is not treated as a complete description of the labor market. Adjacent or unknown role titles can surface through a wildcard path when semantic assessment produces a Base Match of at least 80. This creates controlled discovery without weakening the primary taxonomy.

## Portfolio example

`prompts/expanded_semantic_assessment.example.txt` contains the full assessment contract with fictional Candidate Evidence. The production Candidate Evidence is deliberately not included in this repository.
