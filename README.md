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

### Recommended local AI setup

For the easiest setup, MoneyPulse recommends **Gemma 4 E4B** while keeping the extraction layer provider-independent. **Gemma 4 E2B** is the lower-memory fallback when E4B is too heavy for the host. The application supports both primary local-server workflows:

- **Ollama:** run `ollama pull gemma4:e4b`, start Ollama, and keep the default endpoint `http://localhost:11434`.
- **LM Studio:** download a Gemma 4 E4B-compatible model, start LM Studio's local API server, and use `http://localhost:1234`. MoneyPulse can auto-detect the model identifier exposed by LM Studio.

The desktop configuration dialog includes **Auto-detect Ollama / LM Studio**. Advanced users can select another compatible local model without changing Python source code.


The desktop application defaults to Ollama with `gemma4:e4b`, a lightweight Gemma 4 instruction model intended for local devices. MoneyPulse does not pull model weights automatically. If the configured provider or model is unavailable, component checks and processing fail explicitly rather than silently substituting data.

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

On 2026-09-28, the complete development dependency set installed successfully in a fresh Python 3.12.14 virtual environment. Compilation, dependency consistency (`pip check`), all **50 tests** (including offscreen GUI tests and loopback HTTP protocol tests), the synthetic OCR workflow, and Bandit all passed with Tesseract 5.3.4 and Poppler 26.05.0. Python 3.13 was not run in this environment. The loopback HTTP tests use a deterministic local fixture; they do not verify a real Gemma model. **Live Gemma inference remains unverified**: this environment has no LM Studio server, and its Ollama inference memory is too limited for the Gemma 4 model weights. Run `python examples/run_live_smoke.py` with a working local model server to verify model extraction on your machine.

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

The configuration dialog lets you choose provider, host, and model. It can auto-detect Ollama and LM Studio on their default local endpoints and select a recommended installed model; custom endpoints remain configurable manually.

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

MoneyPulse uses a repository-local release verifier rather than hosted CI as its verification source of truth. The strict release gate creates a temporary virtual environment, installs the declared desktop/development dependencies, checks dependency consistency, compiles the code, launches the GUI through the offscreen smoke tests, runs the complete test suite, executes the real-Tesseract synthetic workflow, and runs Bandit:

```bash
python scripts/verify.py --fresh
```

Linux/macOS users can also run `bash scripts/verify.sh --fresh`; Windows PowerShell users can run `.\\scripts\\verify.ps1 --fresh`. The non-`--fresh` form uses the currently active Python environment for faster development checks.

A real-model release smoke test is separate because it requires a running local model server and downloaded weights. With Gemma 4 E4B or E2B loaded in Ollama or LM Studio, run:

```bash
python scripts/verify.py --fresh --live-model auto
```

Use `--live-model ollama` or `--live-model lm_studio` to require a specific backend. Passing Bandit is security-lint evidence only, not a security or compliance certification.

## Current limitations

- Extraction quality varies by OCR quality, document layout, prompts, and chosen model.
- No fixed extraction-accuracy or speed benchmark is published.
- A live local-model smoke test is environment-dependent and separate from deterministic tests.
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
