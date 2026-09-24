# Changelog

All notable changes to MoneyPulse are documented in this file.

## [Unreleased]

### Fixed
- Restored the intended `LLMParser` constructor after an accidental nested-class definition prevented normal pipeline initialization.
- Corrected the lightweight dependency list so it no longer attempts to install `tkinter` from PyPI and includes OCR imports required by the current code.

### Changed
- Reworked the README around verifiable current behavior and removed unsupported fixed accuracy, speed, compliance, and "zero leakage" claims.
- Expanded `.gitignore` coverage for runtime financial data, local configuration, caches, IDE files, and build artifacts.
- Added the missing PyYAML runtime dependency used by local provider detection.

### Added
- Lightweight CI for syntax/compile checks and deterministic validation tests.
- Contributor and security guidance for an open-source release.

## [v1.0.0] - 2025-08-06

### Initial Release

- Windows-oriented desktop application and PyInstaller build configuration.
- Tesseract OCR for PDF/image extraction.
- Local model parsing experiments and provider-detection utilities.
- Deterministic field validation and human-review flags.
- JSON/CSV exports and development/mock CRM submission flow.
- Optional REST/SOAP CRM connector code.

> Historical release notes have been condensed here during the 2026 documentation cleanup. Performance and compliance statements from early project documentation are not treated as verified benchmarks.

### Versioning

The project uses semantic versioning for tagged releases.
