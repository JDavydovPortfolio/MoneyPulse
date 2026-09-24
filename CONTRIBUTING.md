# Contributing to MoneyPulse

Thanks for your interest in improving MoneyPulse.

## Development setup

1. Fork or clone the repository.
2. Create a virtual environment.
3. Install the dependencies needed for the part of the project you are changing.
4. Create a focused branch.
5. Add or update tests when behavior changes.
6. Open a pull request describing what changed and why.

For the lightweight validation test suite:

```bash
pip install pytest
python -m compileall -q main.py src
pytest -q
```

## Contribution guidelines

- Keep pull requests focused.
- Do not commit real merchant, applicant, banking, tax-ID, or other sensitive financial data.
- Use synthetic or redacted fixtures in tests and examples.
- Do not add fixed performance, accuracy, compliance, or security claims without reproducible evidence.
- Treat model output as untrusted input and preserve deterministic validation/human-review paths.
- Avoid making cloud services mandatory for the core local-first workflow.
- Document new environment variables, external services, and network behavior.

## Issues

Bug reports should include:

- Python and operating-system version;
- the relevant MoneyPulse commit/tag;
- steps to reproduce;
- expected versus actual behavior;
- sanitized logs or synthetic sample data when useful.

Never post credentials or real financial documents in a public issue.
