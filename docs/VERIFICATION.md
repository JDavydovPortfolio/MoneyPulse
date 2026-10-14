# Verification history

This page records historical test evidence for MoneyPulse. It is intentionally separate from the product overview so implementation details and old test environments do not dominate the public README.

## v1.0.0 source baseline — October 12, 2026

The v1.0.0 source candidate was exercised on Windows with Python 3.12 and 3.13, Tesseract OCR, Poppler, the deterministic test suite, synthetic OCR fixtures, and the native desktop workflow.

Recorded checks included:

- fresh Python 3.12 and 3.13 environments;
- 108 tests with no skips in each recorded environment;
- dependency and compilation checks;
- generated synthetic PDF/image OCR;
- desktop launch and document processing;
- local JSON/CSV output;
- a live local-model smoke test through LM Studio;
- targeted review of the tracked tree for common credential/private-material patterns.

The live-model smoke test used the model that was configured at the time: **Gemma 4 E2B QAT Q4_0** through LM Studio. That is historical verification evidence, **not the current MoneyPulse model recommendation**. Current `main` defaults to **Qwen3 8B**, with Qwen3 4B as a lower-memory option.

## Current main

Since v1.0.0, `main` has continued to evolve. Notable changes include:

- Qwen3 8B as the default local extraction model;
- Qwen3-oriented desktop setup guidance;
- deterministic underwriting metrics and configurable MCA pre-screen policy rules;
- an Underwriting view in the desktop application;
- underwriting results persisted in local JSON output;
- updated product documentation and dependency-maintenance settings.

Historical v1.0.0 smoke results should not be presented as test evidence for later changes unless those changes are rerun in the relevant environment. The repository's deterministic tests document expected behavior for current code.

## What the verification record means

The recorded checks demonstrate that the tested source versions completed the listed workflows in their recorded environments. They are not a universal accuracy benchmark for every financial-document layout, model, operating system, or external CRM deployment.

MoneyPulse uses synthetic or fictional fixtures in repository tests and demos; real merchant documents and credentials should not be committed to the repository.
