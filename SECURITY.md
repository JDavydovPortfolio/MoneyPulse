# Security Policy

MoneyPulse implements source-verified extraction, structured-data safeguards, privacy-conscious model connectivity, and controlled downstream integration for financial-document workflows.

## Supported code

Security fixes apply to the latest code on `main` unless a release explicitly states otherwise.

## Reporting a vulnerability

Do **not** include credentials, secrets, real merchant/applicant documents, tax identifiers, bank data, or exploit details containing sensitive data in a public issue.

Use GitHub private vulnerability reporting when available. If it is unavailable, open only a minimal public request for a private contact channel.

A useful private report includes the affected commit/tag, component, synthetic reproduction steps, impact, and remediation ideas if known.

## Data integrity and security controls

**Source-verified extraction.** MoneyPulse uses a deterministic verification gate to reconcile model-proposed fields with their originating OCR chunks before values enter structured output. Equivalent formats such as `$75,000` and `$75000` are normalized for comparison; values without source support are excluded. Document classification relies on explicit source evidence or a narrow, deterministic application-form signature. The resulting fields and provenance are available for evidence-based analyst review.

**Validated CRM integration.** Structural schema validation precedes domain validation and review-state evaluation. Both public external CRM submission entry points require successful deterministic validation, literal boolean `review_approved: true`, and `review_state: approved`. The enterprise submitter also stops transmission if local output preparation fails. These fields represent application review state; integrating applications should bind approvals to authenticated reviewer identities and enforce their own access controls.

**Local-first model connectivity.** HTTP providers support loopback, `.localhost`, private-address, and link-local endpoints by default. Public remote inference requires explicit `allow_remote_llm: true` opt-in. Operators enabling remote inference can evaluate the destination and data-handling requirements before sending OCR-derived content beyond the local/private network.

**Safer data export and display.** CSV exports prefix potentially executable formula strings with an apostrophe, while JSON preserves source values. Integrating tools should retain CSV escaping on import or re-export. OCR and processing-log views display document-derived text as plain text.

**Bounded document processing.** PDFs are rendered one page at a time. Rendering and OCR have operation timeouts and configurable ceilings for input size, PDF page count, and image/rendered-page pixel count. Limits can be tuned for trusted inputs. Keep Tesseract, Poppler, and Python dependencies patched; use OS-level isolation for hostile or unknown documents.

Together, these controls provide layered verification and defensive handling across extraction, serialization, document processing, and external integration.

## Deployment responsibilities

Operators configure and secure model servers, file permissions, generated output, logs, credentials, remote model endpoints, external CRM connections, backups, retention, and operating-system access controls according to their deployment environment.
