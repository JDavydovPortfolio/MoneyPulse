# Verification history

This page records historical test evidence for MoneyPulse. It is separate from the product overview so old environment details do not dominate the README.

## v1.0.0 source baseline — October 12, 2026

The v1.0.0 source candidate was exercised on Windows with Python 3.12 and 3.13, Tesseract OCR, Poppler, the deterministic test suite, synthetic OCR fixtures, and the native desktop workflow.

Recorded checks included fresh Python environments, dependency and compilation checks, generated synthetic PDF/image OCR, desktop launch and processing, local JSON/CSV output, and a live local-model smoke test through LM Studio.

The live-model smoke test used the model configured at that time: **Gemma 4 E2B QAT Q4_0** through LM Studio. That is historical evidence, not the current model recommendation. Current `main` defaults to **Qwen3 8B**, with Qwen3 4B as a lower-memory option.

## Current main

Current behavior includes:

- Qwen3 8B as the default local extraction model;
- source-grounded field extraction that rejects proposed values not supported by OCR text;
- explicit review state before extracted financial fields are relied on downstream;
- no generic underwriting policy engine or autonomous approval/decline recommendation;
- no inference of missing annual revenue, processing volume, years in business, or similar merchant financial facts;
- reviewable local output for downstream underwriting calculations and lender/ISO-specific policy rules.

The later changes on `main` have not been rerun through the historical v1.0.0 Windows verification environment from this chat. Historical smoke results should not be presented as evidence for unrerun current changes. The current tests document the intended source-grounding and validation behavior.

## Meaning of this record

The recorded checks show that the tested source versions completed the listed workflows in their recorded environments. They are not a universal accuracy benchmark for every document layout, model, operating system, or downstream integration.

Repository tests and demos use synthetic or fictional fixtures.
