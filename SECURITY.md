# Security Policy

MoneyPulse can process financially sensitive data. Treat security and privacy issues accordingly.

## Supported code

Security fixes apply to the latest code on `main` unless a release explicitly states otherwise.

## Reporting a vulnerability

Do **not** include credentials, secrets, real merchant/applicant documents, tax identifiers, bank data, or exploit details containing sensitive data in a public issue.

Use GitHub private vulnerability reporting when available. If it is unavailable, open only a minimal public request for a private contact channel.

A useful private report includes the affected commit/tag, component, synthetic reproduction steps, impact, and remediation ideas if known.

## Trust boundaries

Model output is untrusted. MoneyPulse now performs deterministic source grounding before an extracted value is propagated: proposed values must be reconciled with the OCR chunk that produced them. Format-equivalent values such as `$75,000` and `$75000` are normalized for comparison, while ungrounded model values are discarded. Document type is treated as classification data and must either appear directly or satisfy a narrow deterministic application-form signature. This grounding layer reduces plausible-looking hallucinations but does not replace human review.

The application enforces structural schema validation before domain validation and review state. Both public external CRM submission entry points require successful deterministic validation, literal boolean `review_approved: true`, and `review_state: approved`. The enterprise submitter also blocks transmission when local output preparation fails. These metadata checks are not a signed approval or access-control system; embedding applications must own validation and authenticated human approval, rather than accepting flags from untrusted clients.

Model endpoints are local/private by default. HTTP providers accept loopback, `.localhost`, private-address, and link-local endpoints without additional configuration. Remote model endpoints are rejected unless the operator explicitly sets `allow_remote_llm: true`. Enabling that option means OCR-derived document content can leave the local machine/network and should be treated as a deliberate privacy decision.

CSV exports prefix potentially executable formula strings with an apostrophe. JSON preserves source values. Keep escaping intact if another tool imports/re-exports CSV. OCR and processing-log views display document-derived text as plain text.

PDFs are rendered one page at a time. Rendering and OCR have operation timeouts plus configurable ceilings for input file size, PDF page count, and image/rendered-page pixel count. The defaults are intentionally conservative and can be raised for trusted documents. These controls bound routine resource use; the application is still not a malware sandbox. Keep Tesseract/Poppler and Python dependencies patched and process hostile files with appropriate OS isolation.

These controls reduce accidental propagation of malformed or unsupported model output; they are not a guarantee against every security or data-quality failure.

## Deployment responsibilities

MoneyPulse is not a security/compliance certification. Operators are responsible for securing local model servers, file permissions, generated output, logs, credentials/configuration, explicitly enabled remote model endpoints, external CRM endpoints, backups, retention, and operating-system access controls.
