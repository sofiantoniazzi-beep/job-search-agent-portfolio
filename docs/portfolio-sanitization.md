# Portfolio Sanitization Notes

This repository is intentionally maintained separately from the production repository so that its file history contains only portfolio-safe project material.

## Excluded from this repository

- real Candidate Evidence and CV content;
- personal citizenship/work-authorization configuration;
- live Google Sheet IDs;
- Cloud project, bucket, job, service-account, and deployment identifiers;
- API keys, refresh tokens, service-account credentials, and local `.env` files;
- production registry/state files;
- retrieved vacancy datasets and diagnostic exports;
- notebooks or one-off scripts that may contain embedded production outputs.

## Replacements

- `prompts/expanded_semantic_assessment.example.txt` demonstrates the production assessment contract using a fictional candidate.
- `config/candidate.example.json` demonstrates candidate configuration using synthetic values.
- `templates/` contains fictional structures for users replicating the methodology.
- `.env.example` documents required configuration keys without values.

## Public-release checklist

Before changing this repository from private to public:

1. Audit the current tree for credentials, production IDs, personal Candidate Evidence, retrieved vacancy data, and local/state artifacts.
2. Review the full commit history, not only the current files; deleting a sensitive value in a later commit does not remove it from Git history.
3. Review Git author/committer metadata. If a personal email address should not be public, configure a GitHub-provided no-reply address and squash/recreate the portfolio history before release.
4. Run the portfolio test workflow and confirm the reference suite passes from a clean environment.
5. Recheck README screenshots and synthetic examples for accidental real companies, vacancies, identifiers, or candidate facts.
6. Keep the production repository private. Never make it public as a shortcut to publishing the portfolio.

The public repository should contain reusable architecture and methodology, not the original candidate's private operating data.
