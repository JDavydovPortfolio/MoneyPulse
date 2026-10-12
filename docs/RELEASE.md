# Release readiness checklist

MoneyPulse releases are evidence-based. A tag or GitHub release should only be created after the current commit passes the checks below. Historical verification is useful context, but it does not substitute for a fresh release candidate run.

The repository-local verifier is the canonical release gate. GitHub Actions or any other hosted CI service may provide supplemental evidence, but a hosted workflow is **not required** to publish a MoneyPulse source release when the local gate and manual checks below are complete and recorded.

For the first formal GitHub release, the intended version is `v1.0.0`. Draft release notes live in [RELEASE_NOTES_v1.0.0.md](RELEASE_NOTES_v1.0.0.md). Do not publish them or create the tag until the exact release-candidate commit has passed this checklist.

## 1. Clean checkout and environment

- Start from a clean clone of the exact release commit.
- Use supported Python 3.12 and 3.13 interpreters.
- Install Tesseract OCR and Poppler from the operating system package manager.
- Do not place real merchant/applicant documents, credentials, local configuration, generated output, or logs in the checkout.

On Windows, the automated portion of this checklist can be run in one command from a clean checkout:

```powershell
.\scripts\release-gate.ps1
```

That wrapper requires both Python 3.12 and 3.13, verifies Tesseract/Poppler are available, runs the fresh verifier under both interpreters, and runs the live local-model smoke test. It intentionally stops short of claiming release readiness until the manual desktop/privacy/documentation checks below are completed. `-SkipLiveModel` exists for development diagnostics only and prints that the result is insufficient for a release decision.

## 2. Fresh release gate

Run the isolated verifier with both supported Python versions:

```bash
python scripts/verify.py --fresh
python3.13 scripts/verify.py --fresh
```

A release candidate is not ready if dependency installation, `pip check`, compilation, the test suite, the synthetic OCR workflow, GUI smoke coverage, or Bandit fails.

## 3. Headless/core install

Independently verify the lightweight path in a fresh virtual environment:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements-core.txt -c constraints-tested.txt
python -m pip check
python -m src.cli --help
python examples/run_synthetic_demo.py
```

Confirm that desktop, Transformers, and SOAP-only packages are not pulled into a core-only install unless another dependency legitimately requires them.

## 4. Real local-model smoke test

For a release that changes extraction, prompts, provider adapters, configuration, or model defaults, run at least one real-model smoke test with the intended local backend and downloaded model:

```bash
python scripts/verify.py --fresh --live-model auto
```

Use `--live-model ollama` or `--live-model lm_studio` when a specific backend must be exercised. Record the exact model identifier and environment. Do not turn a smoke test into an accuracy benchmark claim.

## 5. Native desktop check

Before distributing a desktop-oriented release, launch `python main.py` on the intended target platform and verify:

- the application starts without a traceback;
- provider/model settings can be saved and reloaded;
- a fictional document can be selected and processed;
- review state remains explicit and unapproved until a human approves it;
- generated output remains local unless an external integration is deliberately configured;
- failures are surfaced rather than silently replaced with synthetic or guessed values.

Linux offscreen Qt tests are useful regression evidence, but they do not replace a native Windows/macOS launch when claiming support for those platforms.

## 6. Privacy and repository audit

Before publishing the release:

- inspect the current tree for `.env` files, credentials, private keys, tokens, local configuration, real financial documents, generated output, and logs;
- inspect newly reachable history since the last recorded audit for the same material;
- if any real secret was ever committed, rotate it before release; deleting it from HEAD is not sufficient;
- keep examples and screenshots synthetic.

The full-history audit record and its limitations are documented in [VERIFICATION.md](VERIFICATION.md).

## 7. Documentation and release notes

Confirm that:

- README installation commands match the actual dependency files and supported Python versions;
- `CHANGELOG.md` describes shipped behavior rather than plans;
- [SETUP.md](SETUP.md), [ARCHITECTURE.md](ARCHITECTURE.md), and [SECURITY.md](../SECURITY.md) match current behavior;
- [RELEASE_NOTES_v1.0.0.md](RELEASE_NOTES_v1.0.0.md) matches the exact verified release candidate;
- experimental or deployment-specific features are labeled as such;
- no compliance, underwriting, accuracy, adoption, or performance claim exceeds the recorded evidence.

## 8. Release decision

Only after the checks above pass should the maintainer create the `v1.0.0` tag and publish the release notes. Record the exact release commit in the release notes and verification record before publishing. PyInstaller artifacts require their own target-platform build and smoke test before being attached to a release.

A passing checklist means the tested source release is reproducible within the recorded scope. It does not certify every document layout, model, operating system, CRM deployment, security property, or regulatory requirement.
