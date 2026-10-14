# MoneyPulse

MoneyPulse is a local-first financial-document processing pipeline for Merchant Cash Advance (MCA) and related operational workflows. It combines OCR, configurable local model extraction, deterministic source/schema/domain validation, reviewable local output, and optional CRM adapters.

**[Setup and troubleshooting](docs/SETUP.md)** · **[Architecture](docs/ARCHITECTURE.md)** · **[Project brief](docs/PROJECT_BRIEF.md)** · **[Contributing](CONTRIBUTING.md)**

![MoneyPulse desktop processing a fictional merchant application](docs/images/moneypulse-demo.png)

Actual desktop screenshot after real Tesseract OCR with the deterministic synthetic fixture provider.

## Try it in a few minutes

Use Python **3.12 or 3.13**, with Tesseract and Poppler installed ([platform instructions](docs/SETUP.md)). No model download is needed for this demo:

```bash
git clone https://github.com/JDavydovPortfolio/MoneyPulse.git
cd MoneyPulse
python -m venv .venv
```

Activate with `source .venv/bin/activate` on Linux/macOS or `.\.venv\Scripts\Activate.ps1` in Windows PowerShell, then:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements-core.txt -c constraints-tested.txt
python examples/run_synthetic_demo.py
```

The demo creates a fictional document, runs real OCR, validates fixture output, and saves local JSON under `output/synthetic_demo/`. Look for `completed`, `passed`, and `ready_for_review`.

For the desktop application, install `requirements.txt` with the same constraints, start Ollama or LM Studio with your model, and run `python main.py`.

## Why it exists

Financial documents often contain sensitive data, while extraction models can return incomplete, malformed, or plausible-looking unsupported output. MoneyPulse is designed around three practical goals:

- let OCR and model inference run locally when a local backend is chosen;
- require model-proposed values to reconcile with the OCR source before they propagate; and
- keep accepted output behind deterministic validation and explicit review boundaries before downstream use.

## Processing flow

```text
document
  -> OCR/source text
  -> local model provider
  -> source-grounded structured extraction
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
| LM Studio | Native local REST API (OpenAI-compatible fallback for older versions) | `http://localhost:1234` |
| llama.cpp | OpenAI-compatible local HTTP | `http://localhost:8080` |
| Hugging Face Transformers | In-process | Optional dependency set |

HTTP model endpoints are restricted to explicit loopback/private/link-local addresses by default. Sending OCR-derived document text to a remote model endpoint requires deliberate `allow_remote_llm: true` configuration.

### Recommended local AI setup

MoneyPulse defaults to **Qwen3 8B** for local extraction. It is available through Ollama as a roughly 5.2 GB Q4_K_M model and is a practical fit for consumer GPUs while providing substantially more capability than the previous ultra-small default. For lower-memory systems, **Qwen3 4B** is the fallback. Tesseract performs OCR; the local model maps OCR text into MoneyPulse's structured schema.

- **Ollama:** run `ollama pull qwen3:8b`, start Ollama, and keep the default endpoint `http://localhost:11434`.
- **LM Studio:** download a Qwen3 8B GGUF, start LM Studio's local API server, and use `http://localhost:1234`. MoneyPulse uses the model identifier exposed by LM Studio.

The desktop configuration dialog includes **Auto-detect Ollama / LM Studio**. Advanced users can select another compatible local model without changing Python source code.

MoneyPulse does not pull model weights automatically. If the configured provider or model is unavailable, component checks and processing fail explicitly rather than silently substituting data.

## Requirements

MoneyPulse needs the following system tools for document OCR:

- Tesseract OCR;
- Poppler for PDF rendering through `pdf2image`.

Python **3.12 or 3.13** is recommended. Python dependency sets are separated by purpose:

- `requirements-minimal.txt` — OCR modules only;
- `requirements-core.txt` — headless pipeline plus local HTTP model providers;
- `requirements.txt` — desktop GUI;
- `requirements-transformers.txt` — optional in-process Transformers provider;
- `requirements-crm.txt` — optional SOAP/OAuth CRM dependencies;
- `requirements-dev.txt` — tests and security linting;
- `requirements-build.txt` — PyInstaller tooling.

## Installation

```bash
git clone https://github.com/JDavydovPortfolio/MoneyPulse.git
cd MoneyPulse
python -m venv .venv
```

Activate the environment, then install the dependency set you need. For the desktop application:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt -c constraints-tested.txt
```

For a headless/local-server setup:

```bash
python -m pip install -r requirements-core.txt -c constraints-tested.txt
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

The configuration dialog lets you choose provider, host, and model. It can auto-detect Ollama and LM Studio on their default local endpoints and select a recommended installed model; custom endpoints remain configurable manually subject to the remote-endpoint safety setting.

Settings persist in git-ignored `config.yaml`. The result selector lets you inspect every document in a completed batch, including failures. Funding and business fields appear alongside merchant/contact details. Document text is displayed as plain text, and new selections/configuration changes are blocked while a worker is active.

## Headless application

```bash
python -m src.cli doctor
python -m src.cli process input --output output
```

The CLI uses the same saved configuration and pipeline. It performs component checks, writes local JSON/CSV, and returns nonzero on invalid inputs, unavailable components, processing failures, or failed domain validation. Use `python -m src.cli --help` for endpoint/model overrides and [SETUP.md](docs/SETUP.md) for exit codes and LM Studio examples.

## Trust boundary and schema

Model output is treated as untrusted. Before a proposed field value is propagated, the extraction layer reconciles it with the OCR source chunk that produced it. Equivalent formatting for amounts and contact identifiers is normalized for comparison; unsupported guesses are discarded while raw attempts remain available in provenance. This grounding layer reduces hallucination propagation but does not prove OCR correctness or document authenticity.

`src/schema.py` then enforces a versioned extraction shape before domain validation can proceed. Unexpected root fields, missing schema fields, wrong nested types, malformed provenance, and unsupported schema versions fail closed.

The extraction result keeps provenance for review, including:

- source file;
- provider and model;
- number of document chunks evaluated;
- raw response attempts by field/chunk.

Raw model-response provenance is not copied into the default downstream CRM-shaped JSON artifact.

CSV exports escape strings that could be evaluated as spreadsheet formulas with a leading apostrophe; the original values remain in JSON.

The current required domain fields are `merchant_name` and `document_type`. Optional financial/contact fields are validated when present; missing optional fields are not invented.

## Long documents and resource limits

Parser input is split into word-bounded chunks. Each field can be attempted across later chunks instead of only the first document chunk. This improves completeness for long documents while retaining per-attempt provenance.

OCR also applies configurable resource ceilings before expensive work: by default **50 MB per input file, 100 PDF pages, and 40 million pixels per image or rendered PDF page**. PDF pages are rendered one at a time, and rendering/OCR calls have timeouts.

## Human review and CRM safety

Validation produces explicit states such as `ready_for_review`, `needs_review`, and `needs_correction`.

The optional enterprise CRM submitter requires all of the following before external transmission:

1. deterministic validation status is `passed`;
2. `review_approved` is explicitly `true`;
3. `review_state` is explicitly `approved`.

Approval is also checked at the public connector entry point. Local output failure blocks enterprise transmission. The desktop and CLI do not expose external CRM submission.

SOAP/OAuth dependencies are lazy-loaded only when those optional integrations are configured. The default local pipeline does not require `zeep` or `requests-oauthlib`.

## Privacy model

MoneyPulse can keep OCR and model inference on the same machine or private network when a local backend is used. Network activity can still occur when:

- Python packages or model weights are downloaded;
- an operator explicitly opts into a remote model endpoint with `allow_remote_llm: true`;
- an optional external CRM integration is explicitly enabled and approved.

Do not commit real merchant/applicant documents, credentials, tax identifiers, bank information, generated outputs, logs, or local configuration. See [SECURITY.md](SECURITY.md).

## Development

Install development dependencies and run:

```bash
python -m compileall -q main.py src tests examples
python -m pytest -q
```

The deterministic test suite uses fakes for model-server behavior; it does not require downloading a large model or starting a live inference server. OCR integration tests use generated fictional images and require Tesseract.

## Current limitations

- Extraction quality varies by OCR quality, document layout, prompts, and chosen model.
- External CRM adapters require deployment-specific testing and credentials.
- PyInstaller configurations are retained, but binary builds should be tested on their target platform.

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
