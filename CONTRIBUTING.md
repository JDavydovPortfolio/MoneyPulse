# Contributing to MoneyPulse

Thanks for helping improve MoneyPulse.

## Development setup

1. Fork or clone the repository.
2. Create and activate a virtual environment.
3. Install `requirements-dev.txt` with `-c constraints-tested.txt`, or the narrower dependency set needed for your change.
4. Create a focused branch.
5. Add/update deterministic tests for behavior changes.
6. Run the complete relevant test suite before opening a pull request.

```bash
python scripts/verify.py
```

Before release-oriented changes are considered complete, run the isolated gate:

```bash
python scripts/verify.py --fresh
```

OCR integration tests use generated fictional images and require Tesseract on the host. Model-provider tests use fakes and must not require a live server or large model download.

PDF integration tests also require Poppler. HTTP integration tests start temporary localhost servers; environments that block local socket binding need that permission to run the full suite. GUI tests use Qt's offscreen platform. Follow [SETUP.md](docs/SETUP.md) for platform tools and troubleshooting.

Dependency updates should deliberately update the tested constraints, pass `pip check`, the fresh verifier, and a current `pip-audit` check. Database/network failures must not be recorded as a clean vulnerability audit. Keep verification scope and interpreter versions explicit in [VERIFICATION.md](docs/VERIFICATION.md).

## Contribution guidelines

- Keep changes focused and reviewable.
- Never commit real merchant/applicant documents, credentials, tax IDs, bank data, generated outputs, or logs.
- Use synthetic/redacted fixtures only.
- Treat all model output as untrusted and preserve structural validation, domain validation, provenance, and human-review boundaries.
- Do not allow validation/review failures to flow automatically to external integrations.
- Do not add fixed speed, accuracy, privacy, compliance, or security claims without reproducible evidence.
- Keep hosted/cloud AI optional; local operation must remain viable.
- Document new external services, credentials, network behavior, and system dependencies.

## Issues

Bug reports should include the commit/tag, Python/OS versions, reproducible steps, expected versus actual behavior, and sanitized logs/fixtures where useful. Never post secrets or real financial documents publicly.
