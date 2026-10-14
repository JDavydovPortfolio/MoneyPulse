# MoneyPulse v1.0.0

MoneyPulse v1.0.0 is the first formal GitHub release of the local-first financial-document processing platform built for Merchant Cash Advance and related underwriting and operations workflows.

## Highlights

- OCR and AI-assisted extraction for merchant applications and supporting financial documents.
- Source-grounded extraction so proposed values are reconciled with OCR text before they are accepted.
- Structured merchant, contact, business, funding, and document data for underwriting and operational review.
- Deterministic schema and domain validation with explicit review states.
- Local JSON and CSV output for downstream analysis and system integration.
- Optional CRM adapters with controlled submission boundaries.
- Desktop and headless CLI workflows.
- Pluggable local-model backends through Ollama, LM Studio, llama.cpp-compatible servers, and optional Transformers.
- Local/private model endpoints by default, with deliberate configuration required for remote endpoints.
- Configurable OCR file, page, and image-size limits.

## Local AI

MoneyPulse supports configurable local models and does not depend on a single model family. The current default is Qwen3 8B through Ollama, with Qwen3 4B available as a lower-memory option. LM Studio users can select a compatible Qwen3 GGUF or another supported local model.

## Installation

Use Python 3.12 or 3.13 with Tesseract OCR and Poppler installed.

For the deterministic synthetic demo:

```bash
git clone https://github.com/JDavydovPortfolio/MoneyPulse.git
cd MoneyPulse
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -r requirements-core.txt -c constraints-tested.txt
python examples/run_synthetic_demo.py
```

For the desktop application, install `requirements.txt` with `constraints-tested.txt`, start a supported local model backend, and run:

```bash
python main.py
```

## Workflow

MoneyPulse is designed to support analysts and underwriters by turning financial documents into structured, reviewable data. Human review remains part of the workflow so extracted information can be checked against source documents before downstream use.

For architecture, setup, and implementation details, see the repository documentation.
