# Security Policy

MoneyPulse processes data that may be financially sensitive. Please treat security and privacy issues with care.

## Supported versions

The project is currently undergoing modernization. Security fixes are applied to the latest code on `main` unless a release explicitly states otherwise.

## Reporting a vulnerability

Please do **not** include secrets, credentials, real merchant documents, tax identifiers, bank-account information, or other sensitive data in a public GitHub issue.

For a vulnerability report, use GitHub's private vulnerability reporting feature if it is enabled for this repository. If private reporting is unavailable, open a minimal public issue requesting a private contact channel without publishing exploit details or sensitive data.

A useful report includes:

- affected commit/tag;
- vulnerable component;
- reproducible steps using synthetic data;
- expected impact;
- suggested remediation, if known.

## Deployment notes

MoneyPulse is not a security or compliance certification. Operators are responsible for securing:

- local model runtimes;
- document storage;
- logs and generated outputs;
- credentials and configuration;
- networked CRM integrations;
- operating-system access controls;
- backups and retention.

Model output should be treated as untrusted until validated.
