# MoneyPulse

MoneyPulse is an experimental, local-first financial-document processing pipeline for Merchant Cash Advance (MCA) and related operational workflows. It combines OCR, configurable local model extraction, deterministic schema/domain validation, reviewable local output, and optional CRM adapters.

> **Status:** active modernization. MoneyPulse is not an underwriting, compliance-certification, or autonomous financial-decision system. Extracted values remain untrusted until deterministic validation and human review are complete.

## Why it exists

Financial documents often contain sensitive data, while extraction models can return incomplete or malformed output. MoneyPulse is designed around two practical goals:

- let OCR and model inference run locally when a local backend is chosen; and
- keep model output behind deterministic validation and explicit review boundaries before downstream use.

## Processing flow

```text
document
  -> OCR/source text
  -> local model provider
  -> versioned structured extraction
  -> deterministic structural validation
  -> deterministic domain validation
  -> human-review state
  -> local JSON/CSV output
  -> optional external CRM only after explicit approval
```

The default pipeline prepares local artifacts. It does not automatically transmit processed documents to an external CRM.

## Supported model providers

| Provider | Mode | Default endpoint |
| --- | --- | --- |
| Ollama | Local HTTP | `http://localhost:11434` |
| LM Studio | OpenAI-compatible local HTTP | `http://localhost:1234` |
| llama.cpp | OpenAI-compatible local HTTP | `http://localhost:8080` |
| Hugging Face Transformers | In-process | Optional dependency set |

The desktop application defaults to Ollama with model name `qwen3:4b`. MoneyPulse does not pull that model automatically. If the configured provider or model is unavailable, component checks and processing fail with an explicit error rather than silently substituting data.

## Requirements

MoneyPulse needs the following system tools for document OCR:

- Tesseract OCR;
- Poppler for PDF rendering through `pdf2image`.

Python dependency sets are separated by purpose:

- `requirements-minimal.txt` — OCR modules only;
- `requirements-core.txt` — headless pipeline plus local HTTP model providers;
- `requirements.txt` — desktop GUI;
- `requirements-transformers.txt` — optional in-process Transformers provider;
- `requirements-crm.txt` — optional SOAP/OAuth CRM dependencies;
- `requirements-dev.txt` — tests and security linting;
- `requirements-build.txt` — PyInstaller tooling.

### Verification environment

On 2026-09-28, all 34 deterministic tests and the synthetic OCR workflow were executed successfully on Python 3.13.5 with Tesseract 5.5.0 and Poppler 25.06.0. Other Python/platform combinations should be treated as **not yet verified by this modernization pass**, even when dependencies support them. A clean dependency installation could not be completed in the verification sandbox because outbound package-index DNS/network access was unavailable; the install commands below are therefore documented but not claimed as freshly verified there.

## Installation

```bash
git clone https://github.com/JDavydovPortfolio/MoneyPulse.git
cd MoneyPulse
python -m venv .venv
```

Activate the environment, then install the dependency set you need. For the desktop application:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

For a headless/local-server setup:

```bash
python -m pip install -r requirements-core.txt
```

For in-process Transformers:

```bash
python -m pip install -r requirements-transformers.txt
```

A network connection may be needed to install packages or model weights. Local-first does not mean every installation or configuration is offline.

## Reproducible synthetic demo

The repository includes a deterministic demo that creates a fictional merchant image, performs real local OCR, injects a deterministic fixture provider instead of a live model, validates the structured result, and writes local output:

```bash
python examples/run_synthetic_demo.py
```

This demo is for pipeline reproducibility. It is **not** a model-accuracy benchmark.

The expected high-level result is:

```text
processing_status: completed
validation_status: passed
review_state: ready_for_review
output destination: local_only
```

## Desktop application

```bash
python main.py
```

The application creates or uses:

- `input/` for documents selected for processing;
- `output/` for local JSON/CSV artifacts;
- `logs/` for local runtime logs.

The configuration dialog lets you choose provider, host, and model. Automatic provider/model discovery exists as a separate component and is not yet integrated directly into the main configuration dialog.

## Trust boundary and schema

Model output is treated as untrusted. `src/schema.py` enforces a versioned extraction shape before domain validation can proceed. Unexpected root fields, missing schema fields, wrong nested types, malformed provenance, and unsupported schema versions fail closed.

The extraction result keeps provenance for review, including:

- source file;
- provider and model;
- number of document chunks evaluated;
- raw response attempts by field/chunk.

Raw model-response provenance is not copied into the default downstream CRM-shaped JSON artifact.

The current required domain fields are `merchant_name` and `document_type`. Optional financial/contact fields are validated when present; missing optional fields are not invented.

## Long documents

Parser input is split into word-bounded chunks. Each field can be attempted across later chunks instead of only the first document chunk. This improves completeness for long documents while retaining per-attempt provenance.

## Human review and CRM safety

Validation produces explicit states such as `ready_for_review`, `needs_review`, and `needs_correction`. Validation never turns extraction into a funding/underwriting decision.

The optional enterprise CRM submitter requires all of the following before external transmission:

1. deterministic validation status is `passed`;
2. `review_approved` is explicitly `true`;
3. `review_state` is explicitly `approved`.

SOAP/OAuth dependencies are lazy-loaded only when those optional integrations are configured. The default local pipeline does not require `zeep` or `requests-oauthlib`.

## Privacy model

MoneyPulse can keep OCR and model inference on the same machine when a local backend is used. Network activity can still occur when:

- Python packages or model weights are downloaded;
- a configured model endpoint is not local;
- an optional external CRM integration is explicitly enabled and approved.

Do not commit real merchant/applicant documents, credentials, tax identifiers, bank information, generated outputs, logs, or local configuration. See [SECURITY.md](SECURITY.md).

## Development and verification

Install development dependencies and run:

```bash
python -m compileall -q main.py src tests examples
python -m pytest -q
```

The deterministic test suite uses fakes for model-server behavior; it does not require downloading a large model or starting a live inference server. OCR integration tests use generated fictional images and require Tesseract.

The repository also contains a Bandit workflow. Passing Bandit is security-lint evidence only; it is not a security or compliance certification.

## Current limitations

- Extraction quality varies by OCR quality, document layout, prompts, and chosen model.
- No fixed extraction-accuracy or speed benchmark is published.
- A live local-model smoke test is environment-dependent and separate from deterministic tests.
- Automatic provider/model discovery is not yet wired into the main provider dialog.
- External CRM adapters require deployment-specific testing and credentials.
- PyInstaller configurations are retained, but binary builds should not be treated as verified until built and tested on their target platform.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Synthetic examples](examples/README.md)
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)
- [Changelog](CHANGELOG.md)

## License

MoneyPulse is licensed under the [MIT License](LICENSE).
