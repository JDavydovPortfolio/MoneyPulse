# Changelog

All notable MoneyPulse changes are documented here.

## [1.0.0] - 2026-10-12

### Source release and verification

- Add formal v1.0.0 release notes and a release workflow around the repository-local verifier.
- Make explicit that GitHub-hosted Actions are supplemental only and are not a prerequisite for publishing a source release.
- Use `v1.0.0` for the first formal source release; retain the 2025 project state below as a historical pre-release baseline.
- Record fresh Windows Python 3.12/3.13 verification, real LM Studio smoke evidence, native desktop processing and local unapproved exports, and current-tree/reachable-history review.
- Record the exact final tagged SHA in GitHub Release metadata after verification, avoiding an impossible tracked-file commit-SHA self-reference.
- Align setup, architecture, and verification documentation with tested behavior and correct PowerShell command formatting.

### October 2026 release-readiness hardening

- Ground model-proposed extraction values against the OCR source before they can propagate into validated output; preserve rejected raw attempts in provenance for review.
- Normalize equivalent amount/contact formatting during grounding while discarding unsupported model guesses.
- Restrict HTTP model providers to explicit loopback/private/link-local endpoints by default; remote endpoints require deliberate `allow_remote_llm: true` configuration.
- Add configurable OCR ceilings for input file size, PDF page count, and image/rendered-page pixels in addition to existing operation timeouts and one-page-at-a-time PDF rendering.
- Add regression coverage for hallucinated field values, remote-endpoint opt-in, and OCR resource limits, and align parser tests with the new source-grounding contract.
- Add an evidence-based release checklist covering fresh installs, core-only smoke tests, live-model checks, native desktop checks, privacy/history review, and documentation accuracy.
- Prepare a manual GitHub-hosted verification workflow that mirrors the local release gate. Two initial hosted attempts were accepted by Actions but received no runner and executed zero steps, so no passing hosted-CI result is claimed.
- Add Dependabot configuration for weekly Python and GitHub Actions dependency update proposals.
- Replace overstated desktop-entry-point wording with a factual local-first description.

### September 29 release hardening

- Neutralize spreadsheet formula prefixes in all CSV string cells while preserving original JSON values.
- Require literal boolean human approval at both public enterprise CRM entry points, and block external submission after local output failure.
- Reject boolean/out-of-range provenance chunk numbers and malformed tax ID, phone, ZIP, revenue, volume, and years-in-business values.
- Render PDFs one page at a time with render/OCR timeouts; verify multi-page PDF extraction with a real generated PDF.
- Add document selection for batch results, display funding/business fields, keep OCR/log text plain, and prevent input/configuration changes or overlapping workers while processing.
- Persist desktop configuration atomically, validate saved settings, and add an explicit example configuration.
- Add a headless `doctor`/`process` CLI with preflight checks, local-only summaries, and nonzero failure exits.
- Upgrade the verifier's pip installer and use recorded dependency constraints for repeatable fresh checks.
- Add platform setup/troubleshooting, a real synthetic desktop screenshot, a verification record, and a maintainer-review project brief.

### Security and trust-boundary changes

- Added strict extraction schema versioning and fail-closed structural validation before domain validation.
- Added extraction provenance for source/provider/model/chunk and raw field attempts.
- Removed arbitrary model-confidence scoring from parser, validator, GUI-facing data, JSON/CSV output, and validation summaries.
- Replaced randomized mock CRM acceptance/IDs with deterministic local-only output preparation.
- Blocked optional external CRM transmission unless deterministic validation passes and explicit human review approval is present.
- Lazy-loaded optional SOAP/OAuth CRM dependencies so unused enterprise integrations cannot break core imports.
- Added timeouts and clearer failure behavior to optional external CRM network calls.

### Extraction and provider fixes

- Use LM Studio's native REST chat endpoint with reasoning disabled, preserving its OpenAI-compatible route for older installations; verified live with Gemma 4 E2B QAT Q4_0.
- Process fields across all document chunks instead of only the first chunk.
- Preserve legitimate colons in extracted values while removing recognized response prefixes.
- Added explicit file/type/corrupt-image OCR failures and clearer Tesseract/Poppler guidance.
- Strengthened local-provider connection checks so configured model availability is checked when possible.
- Switched the desktop default away from an in-process model that could trigger a large download at startup.
- Set the beginner-friendly default to the verified Gemma 4 E2B QAT path, with provider-specific model auto-selection for Ollama and LM Studio; larger compatible models remain optional.
- Removed the unused legacy `llm_optional.py` parser path with its incompatible schema.

### Reproducibility and dependencies

- Added a real-Tesseract, fictional-data end-to-end demo with a deterministic fixture provider.
- Added a cross-platform local release verifier (`scripts/verify.py` with Bash and PowerShell wrappers) that can create a fresh temporary environment, run GUI/OCR/tests/security linting, and optionally smoke-test a real Gemma 4 model through Ollama or LM Studio.
- Created verifier environments through the active interpreter's `python -m venv`, covering relocatable Python distributions such as uv-managed runtimes.
- Keep the repository-local verifier as the canonical release gate; hosted verification is supplemental and must not be reported as passing until a GitHub-hosted runner actually executes it.
- Hardened malformed provider response handling, made failed provider configuration updates atomic, and ensured local output write failures are reported as processing failures.
- Kept processing controls disabled until stopped work has exited, and made factual human review explicit for every model extraction.
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

## Historical pre-release baseline - 2025-08-06

Historical project notes describe the initial Windows-oriented desktop application, OCR pipeline, local-model experiments, validation, and CRM adapter code. No GitHub release artifact or semantic-versioned release is implied by this historical baseline.
