## What changed

<!-- Explain the user-visible or maintenance problem and the smallest fix. -->

## Verification

<!-- List the exact commands/tests you ran and their results. -->

- [ ] Relevant regression tests were added or updated when behavior changed.
- [ ] `python -m pytest -q` passes, or the unrun/failed scope is explained below.
- [ ] Documentation was updated when setup, configuration, trust boundaries, or user-visible behavior changed.

## Trust and privacy

- [ ] No credentials, real financial/applicant data, generated runtime output, logs, or local configuration were added.
- [ ] Model output is still treated as untrusted; source grounding, deterministic validation, provenance, and explicit human review remain intact.
- [ ] Any behavior that can send OCR-derived text outside the local/private environment remains explicit opt-in and is documented/tested.
- [ ] External integration failures cannot bypass validation or review gates.

## Release impact

<!-- Note dependency, configuration, schema, provider, OCR, desktop, security, or release-check implications. Link an issue when useful. -->

## Verification notes / limitations

<!-- Record anything intentionally not tested. Do not present planned or unrun checks as passing. -->
