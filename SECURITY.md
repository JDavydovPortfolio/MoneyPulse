# Security Policy

MoneyPulse can process financially sensitive data. Treat security and privacy issues accordingly.

## Supported code

Security fixes apply to the latest code on `main` unless a release explicitly states otherwise.

## Reporting a vulnerability

Do **not** include credentials, secrets, real merchant/applicant documents, tax identifiers, bank data, or exploit details containing sensitive data in a public issue.

Use GitHub private vulnerability reporting when available. If it is unavailable, open only a minimal public request for a private contact channel.

A useful private report includes the affected commit/tag, component, synthetic reproduction steps, impact, and remediation ideas if known.

## Trust boundaries

Model output is untrusted. The application enforces structural schema validation before domain validation and review state. External CRM transmission is intended to require successful deterministic validation plus explicit human approval.

These controls reduce accidental propagation of malformed model output; they are not a guarantee against every security or data-quality failure.

## Deployment responsibilities

MoneyPulse is not a security/compliance certification. Operators are responsible for securing local model servers, file permissions, generated output, logs, credentials/configuration, external CRM endpoints, backups, retention, and operating-system access controls.
