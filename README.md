# MoneyPulse

MoneyPulse is an experimental, local-first financial document processing pipeline for Merchant Cash Advance (MCA) and related operational workflows. It combines OCR, local model-based extraction, deterministic validation, structured exports, and optional CRM integration.

> **Status:** active modernization. MoneyPulse is a portfolio/open-source project and is not a production underwriting, compliance, or decisioning system. Extracted data should be reviewed before it is used in a financial workflow.

## What it does

The current pipeline is designed around:

1. **Document intake** — PDF, PNG, JPG, and JPEG files.
2. **OCR** — Tesseract-based text extraction with image preprocessing.
3. **Local model parsing** — a provider abstraction supports in-process Hugging Face Transformers, Ollama, LM Studio, and llama.cpp-compatible local endpoints.
4. **Validation** — deterministic checks for fields such as EIN/SSN, ZIP code, phone number, email, state, and requested amount.
5. **Human-review flags** — validation issues are surfaced instead of silently accepted.
6. **Structured output** — JSON and CSV artifacts for downstream workflows.
7. **CRM integration** — a mock/local submission flow is included for development, plus configurable REST/SOAP integration code for external systems.

## Architecture

```mermaid
flowchart LR
    A[PDF / Image] --> B[Tesseract OCR]
    B --> C[Local model provider]
    C --> D[Structured extraction]
    D --> E[Deterministic validation]
    E --> F{Review required?}
    F -->|Yes| G[Human review]
    F -->|No| H[Structured output]
    G --> H
    H --> I[JSON / CSV]
    H --> J[Optional CRM adapter]
```

## Local model providers

MoneyPulse now uses one inference interface across its local backends:

| Provider | Mode | Default endpoint |
| --- | --- | --- |
| Transformers | In-process | n/a |
| Ollama | Local HTTP | `http://localhost:11434` |
| LM Studio | OpenAI-compatible local HTTP | `http://localhost:1234` |
| llama.cpp | OpenAI-compatible local HTTP | `http://localhost:8080` |

The pipeline configuration accepts:

```python
config = {
    "llm_provider": "ollama",
    "llm_host": "http://localhost:11434",
    "model": "your-local-model",
}
```

The legacy `ollama_host` configuration key remains accepted for compatibility.

## Privacy model

MoneyPulse is designed to support local processing. OCR, in-process Transformers models, and supported localhost model servers can operate on the same machine as the documents.

A few important details:

- Python packages and model weights may require network access during initial installation/download unless they are already cached or supplied offline.
- A local HTTP model server is still a network service, even when bound only to localhost.
- Optional CRM connectors make external network requests when configured.
- No claim is made that a particular deployment is compliant with a specific regulation or security standard. Deployment security depends on how the software, model runtime, operating system, storage, and integrations are configured.

## Requirements

- Python 3.9+
- Tesseract OCR
- Poppler for PDF-to-image conversion used by `pdf2image`
- Sufficient memory for the selected local model
- Optional CUDA-capable GPU for faster in-process inference

## Installation

```bash
git clone https://github.com/JDavydovPortfolio/MoneyPulse.git
cd MoneyPulse

python -m venv .venv
```

Activate the environment:

**Windows PowerShell**

```powershell
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux**

```bash
source .venv/bin/activate
```

Install the full application dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

`requirements-minimal.txt` is only for lightweight OCR/module-level experimentation. It does **not** contain the GUI or local-model stack required to launch `python main.py`.

## Run

```bash
python main.py
```

The desktop application creates/uses:

- `input/` for source documents
- `output/` for generated JSON/CSV data
- `logs/` for local runtime logs

Do not commit real merchant, applicant, banking, tax-ID, or other sensitive documents to the repository.

## Development

The deterministic test suite does not download large ML models or call a real model server.

```bash
pip install pytest
python -m compileall -q main.py src
python -m pytest -q
```

The repository also includes a Bandit security-scanning workflow configuration in `.github/workflows/bandit.yml`.

## Current limitations

MoneyPulse is under active modernization. In the current codebase:

- model output is not a substitute for human verification;
- accuracy varies by document quality, OCR quality, document layout, and model choice;
- the default CRM submission flow is a mock implementation intended for development/testing;
- external CRM integrations require deployment-specific configuration and testing;
- the desktop configuration screen supports provider/host/model selection, while automatic model discovery remains a separate component;
- there is no published benchmark supporting a fixed extraction-accuracy or speed claim.

## Roadmap

Near-term work includes:

- integrate detected model lists directly into the main desktop configuration dialog;
- add synthetic/sample financial documents for reproducible demos;
- add schema validation for model output;
- expand OCR-independent extraction tests;
- improve error handling and observability;
- document secure deployment patterns;
- add reproducible benchmarks before publishing performance claims.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Bug reports and focused pull requests are welcome.

## Security

Please see [SECURITY.md](SECURITY.md). Do not open a public issue containing real financial data, credentials, tax identifiers, bank-account information, or other sensitive information.

## License

MoneyPulse is licensed under the [MIT License](LICENSE).
