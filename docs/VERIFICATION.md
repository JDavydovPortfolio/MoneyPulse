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

### October 19, 2026 verification

Current source changes were checked again on Windows 11 (build 26300) with Tesseract 5.4.0.20240606 and Poppler 26.07.0. Historical Gemma smoke results are kept separate from the current Qwen model configuration.

| Check | Observed result |
| --- | --- |
| Fresh Python 3.12.13 environment before the final extraction fixes | 109 tests passed, no skips; dependency consistency, compilation, synthetic OCR demo and Bandit passed |
| Fresh Python 3.13.15 environment before the final extraction fixes | 109 tests passed, no skips; the same required checks passed |
| Full suite after the final extraction fixes | 119 tests passed, no skips, in the existing desktop verification environment |
| Independent core-only install | CLI help, dependency consistency and real synthetic OCR passed; PySide6, Torch, Transformers and Zeep absent |
| Dependency database audit | pip-audit 2.10.1 reported no known vulnerabilities in the installed tested desktop/development/audit environment on this date |
| Displayed Windows desktop with fixture provider | Programmatic file selection and the real worker completed Tesseract OCR; OCR preview, structured fields and review state were inspected; local JSON stayed unapproved and CSV export succeeded |
| Normal application entry point | `main.main()` launched a displayed Windows application in a separate process and reloaded saved LM Studio settings; the unavailable-model error was visible before a model was loaded |
| Qwen3 4B Q4_K_M through LM Studio | Did not pass: merchant, requested amount and email matched, but the model proposed an unsupported document type; source grounding discarded it and domain validation failed. The native live desktop attempt also failed validation. Both kept output local and unapproved |
| Qwen3 8B Q4_K_M through LM Studio | The CLI smoke passed after classification recovery. The displayed native Windows workflow then passed after correcting empty-answer handling: real OCR, extracted fields, validation, visible review state, local unapproved JSON and CSV export. Absent business type, years in business and processing volume stayed blank after the final field-grounding fix |

The desktop check used Qt's native Windows platform with the same application style as the normal entry point. It used the deterministic synthetic fixture provider and does not establish model accuracy or manual file-picker interaction. The README screenshot shows that current interface with fictional data.

The first complete wrapper attempt passed the deterministic checks but failed its live-model stage because neither Ollama nor LM Studio was serving a usable extraction model. That is an infrastructure failure, not a live-model pass. After installation, Qwen3 4B exposed the classification limitation recorded above. Neither result is counted as a passing live-model gate. Repeated classification requests reproduced the unsupported label without changing application code or weakening validation.

The final fixes add a review-flagged document-type fallback using explicit business-name and requested-funding-amount labels, with conflicting invoice/statement/agreement/contract wording blocking that fallback. LM Studio's empty output list now preserves an absent field, while reasoning-only or malformed responses still fail. Business type requires an explicit type/industry label. Regression tests cover these boundaries. The native workflow uses programmatic file selection and the actual application worker; it is not a manual file-picker test or an accuracy benchmark.

### October 19 privacy/history review

A targeted scan covered 143 locally reachable/fetched commits, 378 unique historical blobs and 73 current tracked paths before this documentation update. Checks included private-key headers, GitHub/AWS/OpenAI/Google/Slack token formats, JWTs and literal credential assignments. A literal-credential match in a historical README was reviewed and identified as example placeholder strings; no real credential was identified by these checks. Current tracked paths were also reviewed for real documents, local configuration, private keys and generated outputs/logs, with none identified.

This covers the reachable local/fetched history and checked patterns, not unreachable server objects or every possible credential format. It is not proof that secrets never existed. Historical machine-specific paths, build/editor metadata, bytecode and tracebacks remain in old history; no history rewrite was performed. Runtime configuration, outputs and logs remain excluded from the tracked tree.

## Meaning of this record

The recorded checks show that the tested source versions completed the listed workflows in their recorded environments. They are not a universal accuracy benchmark for every document layout, model, operating system, or downstream integration.

Repository tests and demos use synthetic or fictional fixtures.
