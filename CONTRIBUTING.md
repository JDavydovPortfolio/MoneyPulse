# Contributing to MoneyPulse

Thanks for helping improve MoneyPulse.

## Development setup

1. Fork or clone the repository.
2. Create and activate a virtual environment.
3. Install `requirements-dev.txt` or the narrower dependency set needed for your change.
4. Create a focused branch.
5. Add/update deterministic tests for behavior changes.
6. Run the complete relevant test suite before opening a pull request.

```bash
python -m pip install -r requirements-dev.txt
python -m compileall -q main.py src tests examples
python -m pytest -q
```

OCR integration tests use generated fictional images and require Tesseract on the host. Model-provider tests use fakes and must not require a live server or large model download.

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
