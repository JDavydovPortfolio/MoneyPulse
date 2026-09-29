# Security Policy

MoneyPulse can process financially sensitive data. Treat security and privacy issues accordingly.

## Supported code

Security fixes apply to the latest code on `main` unless a release explicitly states otherwise.

## Reporting a vulnerability

Do **not** include credentials, secrets, real merchant/applicant documents, tax identifiers, bank data, or exploit details containing sensitive data in a public issue.

Use GitHub private vulnerability reporting when available. If it is unavailable, open only a minimal public request for a private contact channel.

A useful private report includes the affected commit/tag, component, synthetic reproduction steps, impact, and remediation ideas if known.

## Trust boundaries

Model output is untrusted. The application enforces structural schema validation before domain validation and review state. Both public external CRM submission entry points require successful deterministic validation, literal boolean `review_approved: true`, and `review_state: approved`. The enterprise submitter also blocks transmission when local output preparation fails. These metadata checks are not a signed approval or access-control system; embedding applications must own validation and authenticated human approval, rather than accepting flags from untrusted clients.

CSV exports prefix potentially executable formula strings with an apostrophe. JSON preserves source values. Keep escaping intact if another tool imports/re-exports CSV. OCR and processing-log views display document-derived text as plain text.

PDFs are rendered one page at a time. Rendering and OCR have timeouts, but the application is not a malware sandbox or a complete resource-quota system. Keep Tesseract/Poppler and Python dependencies patched; process untrusted documents with appropriate OS isolation.

These controls reduce accidental propagation of malformed model output; they are not a guarantee against every security or data-quality failure.

## Deployment responsibilities

MoneyPulse is not a security/compliance certification. Operators are responsible for securing local model servers, file permissions, generated output, logs, credentials/configuration, external CRM endpoints, backups, retention, and operating-system access controls.
