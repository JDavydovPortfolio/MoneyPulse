# AGENTS.md

This file defines repository-level engineering guidance for coding agents and automated maintainers working on MoneyPulse.

## Project purpose

MoneyPulse is a local-first financial-document processing pipeline. The core flow is OCR -> local/model-backed structured extraction -> source grounding -> deterministic schema/domain validation -> explicit human review -> local output, with optional external integrations behind separate approval gates.

Preserve working software. Prefer small, evidence-backed changes over rewrites or architectural churn.

## Non-negotiable trust boundaries

1. **Model output is untrusted.** Do not bypass source grounding, versioned schema validation, domain validation, provenance, or explicit review state.
2. **Never invent missing financial/contact values.** Unsupported model guesses must be rejected rather than silently corrected or synthesized.
3. **Remote inference is opt-in.** HTTP model providers must remain local/private by default. Any path that can send OCR-derived text to a public endpoint must require deliberate configuration and documentation.
4. **External transmission requires approval.** Do not let CRM/integration failures, truthy non-booleans, or alternate entry points bypass deterministic validation and explicit human approval.
5. **Synthetic fixtures only.** Never add real merchant/applicant documents, tax IDs, bank data, credentials, generated runtime output, logs, or local configuration to the repository.
6. **No unsupported claims.** Do not add accuracy, speed, privacy, security, underwriting, compliance, adoption, or benchmark claims without reproducible evidence.

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

For release-oriented changes, use the repository verifier:

```bash
python scripts/verify.py --fresh
```

Run the fresh gate with supported Python 3.12 and 3.13 before tagging a source release. Changes to extraction, prompts, provider adapters, or model defaults also require a real local-model smoke test on the intended backend. Desktop releases require a native target-platform launch/workflow check. See `docs/RELEASE.md` and `docs/VERIFICATION.md`.

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
