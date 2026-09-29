# MoneyPulse project brief

## Problem and users

Merchant intake workflows turn sensitive financial documents into structured records. OCR can misread source text, and model extraction can invent or misformat values. MoneyPulse gives developers and operations teams a local-first reference pipeline where model output remains untrusted and human review is explicit.

## Reusable value

- A shared model-provider interface for Ollama, LM Studio, llama.cpp-compatible servers, and optional Transformers.
- Versioned extraction schema, per-field/chunk provenance, and deterministic domain validation.
- Reviewable local JSON and spreadsheet-safe CSV, with external CRM submission gated separately.
- Real OCR synthetic demos that outsiders can evaluate without private documents or model downloads.
- Desktop and headless paths with regression tests and a repository-local fresh-environment verifier.

These are implemented components. Extraction accuracy on a representative real-document corpus, packaged desktop installers, and deployment-specific CRM integrations are not claimed as completed benchmarks or certifications.

## Demonstration

1. Follow the [quick start](../README.md#try-it-in-a-few-minutes).
2. Run the synthetic OCR demo and inspect the unapproved local JSON.
3. Run the fresh verifier to evaluate the GUI, PDF/image OCR, HTTP provider contracts, and failure boundaries.
4. Start a real local model and run the separate live-model smoke test.
5. Read [architecture](ARCHITECTURE.md) and [verification](VERIFICATION.md) to distinguish deterministic validation from model factual accuracy.

## Maintenance evidence

Repository history records provider unification, schema/approval boundaries, output-failure handling, compatibility tests, documentation corrections, and local release verification. The September 29 hardening work additionally addresses spreadsheet formula injection, non-boolean CRM approval, direct connector bypass, batch review, persistent configuration, and bounded PDF rendering.

Maintainer responsibility should be supported by these actual changes and ongoing review, triage, dependency maintenance, and releases. No external usage, downloads, stars, or contributors are manufactured or asserted here. Prepared release checks are not represented as published releases.

## Codex for Open Source positioning

The [current OpenAI application](https://openai.com/form/codex-for-oss/) asks for a public repository, primary/core maintainer role, and a qualification explanation capped at 500 characters. It considers repository usage, ecosystem importance, and active maintenance, and allows applicants to explain ecosystem value when other signals are less established. Read the live form and terms again before submission.

The strongest defensible case is the reusable local-inference and validation architecture, reproducible evaluation without sensitive data, and substantive maintenance evidence. Software readiness does not establish broad adoption or guarantee selection.

### Draft qualification text — for maintainer review, not submitted

> MoneyPulse is a local-first financial-document pipeline with interchangeable model providers, versioned schemas, deterministic validation, explicit review states, and gated CRM export. Its reusable trust boundaries and synthetic OCR demos let developers evaluate document automation without private data. Fresh-install checks cover desktop/headless workflows and failure paths. The public history shows substantive provider, security, testing, and dependency maintenance.

### Draft API-credit use — for maintainer review, not submitted

> API credits would support MoneyPulse maintenance: reviewing code changes, reproducing bugs with synthetic fixtures, expanding malformed-output and approval-boundary tests, analyzing dependency vulnerabilities, and preparing verified releases. Private financial documents would not be used as evaluation fixtures. Credits would support development and maintenance; users can continue running document inference locally.

Do not add adoption statistics without a verified source. Confirm the applicant's GitHub role, public profile, account email, and any organization ID privately before completing the form. Neither draft authorizes submitting the application or posting public messages.
