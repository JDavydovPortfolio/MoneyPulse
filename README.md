# MoneyPulse

**Local-first AI document processing for Merchant Cash Advance underwriting and operations.**

MoneyPulse converts merchant applications and supporting financial documents into structured, source-backed data for analyst and underwriter review. It combines OCR, configurable local-model field extraction, source grounding, deterministic validation, local JSON/CSV output, and optional downstream CRM integrations.

**Document → OCR → source-backed field extraction → validation → analyst/underwriter review → downstream workflow**

**[Setup and troubleshooting](docs/SETUP.md)** · **[Architecture](docs/ARCHITECTURE.md)** · **[Project brief](docs/PROJECT_BRIEF.md)** · **[Contributing](CONTRIBUTING.md)**

![MoneyPulse desktop processing a fictional merchant application](docs/images/moneypulse-demo.png)

Actual desktop screenshot using a generated fictional document and real Tesseract OCR.

## What MoneyPulse does

- Reads PDF and image documents with Tesseract OCR.
- Uses Ollama, LM Studio, llama.cpp-compatible servers, or optional Transformers to map OCR text into structured fields.
- Accepts a model-proposed value only when it can be reconciled with the OCR source text.
- Extracts merchant, contact, address, funding, and business fields when those values are present in the source document.
- Applies deterministic schema and domain validation.
- Preserves provenance so extracted values can be checked against the source.
- Produces local JSON and CSV artifacts for review and downstream workflows.
- Supports optional CRM integrations behind explicit approval gates.

Financial fields remain source-backed: if a value is not supported by OCR text, MoneyPulse leaves the field missing instead of filling it by model inference.

## Why it exists

MCA underwriting often starts with merchant applications, scans, images, and supporting financial documents. Before an underwriter can evaluate a file, information has to be read, re-keyed, normalized, and checked against the original source.

MoneyPulse automates that intake and data-preparation layer so analysts can move from raw documents to structured, reviewable data while keeping source evidence attached to the workflow.

## Processing flow

```text
document
  -> OCR/source text
  -> local model proposes explicit field values
  -> source grounding
  -> schema + domain validation
  -> analyst / underwriter review
  -> local JSON / CSV
  -> optional downstream CRM / underwriting workflow
```

The local model acts as a field-extraction aid. MoneyPulse independently checks proposed values against OCR text before allowing them to propagate through the pipeline.

## Why use a local model?

OCR answers **what text is on the page**. It does not reliably answer **which pieces of that text belong in which structured business fields** when forms, labels, ordering, and layouts vary across ISOs and document types.

The local model is used only for that semantic mapping step: it proposes values for fields such as merchant name, requested amount, address, annual revenue, years in business, or processing volume when those values are explicitly present in the OCR text. MoneyPulse then checks the proposal against the source text before accepting it.

This gives MoneyPulse two practical advantages:

- **Template flexibility:** different forms can use different labels and layouts without requiring a custom parser for every document template.
- **Local handling of sensitive data:** inference can run on the operator's machine or private network instead of requiring merchant document text to be sent to a hosted AI API.

The model is not used to invent missing financial facts, estimate revenue from a raw bank statement, calculate merchant risk, or make an approval/decline decision. Known rigid templates can also be handled with deterministic extraction; the local model is most useful when document wording and layout vary.

## Supported local-model providers

| Provider | Mode | Default endpoint |
| --- | --- | --- |
| Ollama | Local HTTP | `http://localhost:11434` |
| LM Studio | Local REST API | `http://localhost:1234` |
| llama.cpp | OpenAI-compatible local HTTP | `http://localhost:8080` |
| Hugging Face Transformers | In-process | Optional dependency set |

MoneyPulse defaults to **Qwen3 8B** for local extraction. **Qwen3 4B** is a lower-memory option.

## Quick start

Use Python **3.12 or 3.13** with Tesseract and Poppler installed.

```bash
git clone https://github.com/JDavydovPortfolio/MoneyPulse.git
cd MoneyPulse
python -m venv .venv
```

Activate the environment, then install the core dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements-core.txt -c constraints-tested.txt
python examples/run_synthetic_demo.py
```

For the desktop application:

```bash
python -m pip install -r requirements.txt -c constraints-tested.txt
python main.py
```

For Ollama:

```bash
ollama pull qwen3:8b
```

LM Studio users can load a compatible Qwen3 GGUF and start the local API server on port 1234.

## Synthetic demo

The repository includes a deterministic demo built from fictional data. It creates a synthetic merchant document, performs real OCR, runs the extraction and validation pipeline, and writes local output.

The fixture provider is deterministic so the demo can exercise the pipeline without downloading a live model.

## Desktop application

The PySide6 desktop app supports document selection and drag/drop, OCR preview, structured field review, validation issues and review state, provider/model configuration, local JSON/CSV output, and batch result inspection.

Settings persist in git-ignored `config.yaml`.

## Headless use

```bash
python -m src.cli doctor
python -m src.cli process input --output output
```

The CLI uses the same extraction and validation pipeline as the desktop application.

## Source grounding and validation

Model output is treated as proposed data. Before a field value can propagate, MoneyPulse checks that it is supported by the OCR source text.

Examples include matching requested funding amounts near request/funding language, matching revenue values near revenue language, matching processing-volume values near processing/volume language, and normalizing identifiers/contact fields before comparing them with OCR text.

Source grounding is followed by versioned schema validation and deterministic domain checks. The resulting structured data and provenance remain available for analyst/underwriter review before downstream use.

## Privacy model

When a local backend is selected, OCR and model inference can remain on the operator's machine or private network. Remote model endpoints require explicit `allow_remote_llm: true` configuration.

Network activity can still occur when packages or model weights are downloaded or when an optional external integration is intentionally configured.

Do not commit real merchant/applicant documents, credentials, tax identifiers, bank information, generated outputs, logs, or local configuration. See [SECURITY.md](SECURITY.md).

## Requirements

System dependencies:

- Tesseract OCR;
- Poppler for PDF rendering through `pdf2image`.

Python dependency sets are separated by purpose:

- `requirements-minimal.txt` — OCR modules;
- `requirements-core.txt` — headless pipeline and local HTTP providers;
- `requirements.txt` — desktop GUI;
- `requirements-transformers.txt` — optional in-process Transformers provider;
- `requirements-crm.txt` — optional CRM dependencies;
- `requirements-dev.txt` — tests/security tooling;
- `requirements-build.txt` — packaging tooling.

## Development

```bash
python -m compileall -q main.py src tests examples
python -m pytest -q
```

The deterministic provider tests use generated fictional data and do not require a live model server. OCR integration tests require Tesseract.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Setup and troubleshooting](docs/SETUP.md)
- [Project brief](docs/PROJECT_BRIEF.md)
- [Synthetic examples](examples/README.md)
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)
- [Changelog](CHANGELOG.md)

## License

MoneyPulse is licensed under the [MIT License](LICENSE).
