# AGENTS.md

This file defines repository-level engineering guidance for coding agents and automated maintainers working on MoneyPulse.

## Project purpose

MoneyPulse is a local-first financial-document intelligence pipeline for Merchant Cash Advance underwriting operations. The core flow is OCR -> model-assisted structured extraction -> source grounding -> deterministic schema/domain validation -> human review -> optional deterministic calculations on approved values -> local output, with optional downstream integrations.

Preserve working software. Prefer small, evidence-backed changes over architectural churn.

## Non-negotiable trust boundaries

1. **Model output is untrusted.** Do not bypass source grounding, versioned schema validation, domain validation, provenance, or explicit review state.
2. **Never invent missing financial/contact values.** Unsupported model guesses must be rejected rather than silently corrected, synthesized, estimated, or inferred.
3. **The model is not an underwriting oracle.** It may help map OCR text to explicit source fields; it must not infer annual revenue, processing volume, years in business, approval criteria, risk grades, or credit decisions from unsupported context.
4. **Derived calculations require reviewed inputs.** Arithmetic based on merchant financial fields must not run as though fresh OCR/model extraction were already approved. Missing reviewed inputs stay missing.
5. **Remote inference is opt-in.** HTTP model providers remain local/private by default. Any path that sends OCR-derived text to a public endpoint requires deliberate configuration and documentation.
6. **External transmission stays explicit.** CRM/network integrations must not happen implicitly as a side effect of local processing.
7. **Synthetic fixtures only.** Never add real merchant/applicant documents, tax IDs, bank data, credentials, generated runtime output, logs, or local configuration to the repository.
8. **No unsupported claims.** Do not add accuracy, speed, privacy, security, compliance, underwriting-decision, adoption, or benchmark claims without reproducible evidence.

## Dependency boundaries

- `requirements-minimal.txt`: OCR-only pieces.
- `requirements-core.txt`: headless pipeline + local HTTP providers.
- `requirements.txt`: desktop GUI.
- `requirements-transformers.txt`: optional in-process Transformers.
- `requirements-crm.txt`: optional CRM/SOAP/OAuth stack.
- `requirements-dev.txt`: test/security tooling.
- `requirements-build.txt`: packaging tooling.
- `constraints-tested.txt`: recorded tested versions, not a universal lock file.

Do not make optional stacks mandatory for core imports. Dependency updates must be tested in the scope they affect. Major upgrades should not be merged solely because automation opened a pull request.

## Verification

For ordinary changes, run the narrowest relevant tests first, then the full deterministic suite when practical:

```bash
python -m compileall -q main.py src tests examples
python -m pytest -q
```

For clean-environment verification:

```bash
python scripts/verify.py --fresh
```

Changes to extraction, prompts, provider adapters, or model defaults should also receive a real local-model smoke test on the intended backend when practical. Desktop changes should be exercised on the target platform. Historical verification records live in `docs/VERIFICATION.md`.

A test that was not run is **not** a pass. Record infrastructure failures separately from software failures.

## Change discipline

- Reproduce a defect before fixing it when feasible.
- Add a regression test for behavioral fixes.
- Keep public interfaces backward-compatible unless the change is deliberate and documented.
- Keep README/setup/security/architecture text aligned with actual behavior.
- Do not replace functioning components simply because another design is fashionable or theoretically cleaner.
- Keep commits substantive and professionally scoped; do not manufacture activity.

## Public communication boundary

Engineering automation may modify code, tests, documentation, dependency configuration, and release-preparation files when authorized. It must not post issue replies, pull-request comments/reviews, discussion posts, application text, email, or social messages under the maintainer's identity without explicit approval of the exact text.

Read-only inspection and preparation of private drafts are allowed. Public-facing text that speaks as the maintainer should be drafted for review rather than posted automatically.
