# Changelog

All notable MoneyPulse changes are documented here.

## [Unreleased]

### Security and trust-boundary changes

- Added strict extraction schema versioning and fail-closed structural validation before domain validation.
- Added extraction provenance for source/provider/model/chunk and raw field attempts.
- Removed arbitrary model-confidence scoring from parser, validator, GUI-facing data, JSON/CSV output, and validation summaries.
- Replaced randomized mock CRM acceptance/IDs with deterministic local-only output preparation.
- Blocked optional external CRM transmission unless deterministic validation passes and explicit human review approval is present.
- Lazy-loaded optional SOAP/OAuth CRM dependencies so unused enterprise integrations cannot break core imports.
- Added timeouts and clearer failure behavior to optional external CRM network calls.

### Extraction and provider fixes

- Process fields across all document chunks instead of only the first chunk.
- Preserve legitimate colons in extracted values while removing recognized response prefixes.
- Added explicit file/type/corrupt-image OCR failures and clearer Tesseract/Poppler guidance.
- Strengthened local-provider connection checks so configured model availability is checked when possible.
- Switched the desktop default away from an in-process model that could trigger a large download at startup; local HTTP providers remain configurable.
- Removed the unused legacy `llm_optional.py` parser path with its incompatible schema.

### Reproducibility and dependencies

- Added a real-Tesseract, fictional-data end-to-end demo with a deterministic fixture provider.
- Expanded deterministic regression coverage for schema, parser, provider, OCR, pipeline, and CRM boundaries.
- Split OCR/core/GUI/Transformers/CRM/dev/build dependencies into purpose-specific requirements files.
- Corrected stale input-directory content that contained a machine-specific traceback/path.
- Reworked build scripts/spec comments to remove fixed-size and portability claims; binary builds remain separately verifiable artifacts.

### Earlier modernization in this cycle

- Restored the intended `LLMParser` constructor after an accidental nested-class definition.
- Added a common provider interface for Transformers, Ollama, LM Studio, and llama.cpp-compatible endpoints.
- Added provider/endpoint/model selection in desktop settings and provider detection helpers.
- Reworked README/security/contributor guidance around local-first behavior and unsupported-claim removal.
- Expanded `.gitignore` coverage and added synthetic examples/architecture documentation.

## [v1.0.0] - 2025-08-06

Historical project notes describe the initial Windows-oriented desktop application, OCR pipeline, local-model experiments, validation, and CRM adapter code. No current GitHub release artifact is implied by this changelog entry; consult repository tags/releases directly before relying on a packaged version.
