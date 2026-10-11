# MoneyPulse project brief

## Problem and users

Merchant intake workflows turn sensitive financial documents into structured records. OCR can misread source text, and model extraction can invent or misformat values. MoneyPulse gives developers and operations teams a local-first reference pipeline where model output remains untrusted and human review is explicit.

## Reusable value

- A shared model-provider interface for Ollama, LM Studio, llama.cpp-compatible servers, and optional Transformers.
- Source-grounded extraction that reconciles model-proposed values with their OCR source before propagation, while retaining raw attempts in provenance for review.
- Versioned extraction schema, deterministic structural/domain validation, and explicit review states.
- Local/private HTTP model endpoints by default, with deliberate opt-in required before OCR-derived text can be sent to a remote model endpoint.
- Configurable OCR resource ceilings plus one-page-at-a-time PDF rendering and operation timeouts.
- Reviewable local JSON and spreadsheet-safe CSV, with external CRM submission gated separately.
- Real OCR synthetic demos that outsiders can evaluate without private documents or model downloads.
- Desktop and headless paths with regression tests and a repository-local fresh-environment verifier.

These are implemented components. Extraction accuracy on a representative real-document corpus, packaged desktop installers, deployment-specific CRM integrations, and broad external adoption are not claimed as completed benchmarks, certifications, or usage evidence.

## Demonstration

1. Follow the [quick start](../README.md#try-it-in-a-few-minutes).
2. Run the synthetic OCR demo and inspect the unapproved local JSON.
3. Run the fresh verifier to evaluate the GUI, PDF/image OCR, HTTP provider contracts, and failure boundaries.
4. Start a real local model and run the separate live-model smoke test.
5. Read [architecture](ARCHITECTURE.md), [verification](VERIFICATION.md), and the [release checklist](RELEASE.md) to distinguish deterministic validation from model factual accuracy and recorded evidence from release requirements.

## Maintenance evidence

Repository history records provider unification, schema/approval boundaries, output-failure handling, compatibility tests, documentation corrections, and local release verification. The September 29 hardening work additionally addresses spreadsheet formula injection, non-boolean CRM approval, direct connector bypass, batch review, persistent configuration, and bounded PDF rendering.

The October hardening adds source-grounded extraction, explicit remote-endpoint opt-in, OCR file/page/pixel ceilings, regression tests for those boundaries, release-readiness documentation, a manual hosted-verification workflow, and dependency-update configuration. The latest October grounding/resource-limit change set has focused regression and compilation evidence; the last complete fresh-environment release gate remains the September 29 record until the current release candidate is rerun through [RELEASE.md](RELEASE.md).

Maintainer responsibility should be supported by these actual changes and ongoing review, triage, dependency maintenance, and releases. No external usage, downloads, stars, or contributors are manufactured or asserted here. Prepared release checks are not represented as published releases.

## Codex for Open Source positioning

The [current OpenAI application](https://openai.com/form/codex-for-oss/) asks for a public repository, primary/core maintainer role, and a qualification explanation capped at 500 characters. It considers repository usage, ecosystem importance, and active maintenance, and allows applicants to explain ecosystem value when other signals are less established. Read the live form and terms again immediately before submission.

The strongest defensible case is the reusable local-inference and trust-boundary architecture, reproducible evaluation without sensitive data, and substantive maintenance evidence. Software readiness does not establish broad adoption or guarantee selection.

### Draft qualification text — for maintainer review, not submitted

> MoneyPulse is a local-first financial-document pipeline with interchangeable model providers, source-grounded extraction, versioned schemas, deterministic validation, and explicit human review. Synthetic OCR demos let others evaluate it without private data. The public history shows substantive provider, security, testing, dependency, and release-maintenance work; recorded fresh-install checks cover the September baseline, with focused regressions for the latest hardening.

### Draft API-credit use — for maintainer review, not submitted

> API credits would support MoneyPulse maintenance: reviewing code changes, reproducing bugs with synthetic fixtures, expanding malformed-output and approval-boundary tests, analyzing dependency vulnerabilities, and preparing verified releases. Private financial documents would not be used as evaluation fixtures. Credits would support development and maintenance; users can continue running document inference locally.

Do not add adoption statistics without a verified source. Confirm the applicant's GitHub role, public profile, account email, and any organization ID privately before completing the form. Neither draft authorizes submitting the application or posting public messages.
