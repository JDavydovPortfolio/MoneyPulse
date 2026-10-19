# MoneyPulse project brief

## Overview

MoneyPulse is a local-first document-intelligence pipeline for Merchant Cash Advance underwriting operations. It converts merchant applications and supporting financial documents into structured, source-backed data for analyst and underwriter review.

The project combines OCR, configurable local-model extraction, source grounding, deterministic schema/domain validation, desktop/headless workflows, reviewable local output, and optional CRM integration.

## Problem

MCA teams routinely receive merchant information in PDFs, scans, images, applications, and supporting documents. Before an underwriter can evaluate a file, that information often has to be read, re-keyed, normalized, and checked against the original source.

MoneyPulse automates that intake and data-preparation layer while preserving source evidence.

## Core workflow

```text
merchant documents
  -> OCR/source text
  -> local model proposes explicit field values
  -> source grounding
  -> schema + domain validation
  -> analyst / underwriter review
  -> local structured output
  -> optional downstream CRM / underwriting workflow
```

## Extraction boundary

The local model maps OCR text into structured fields. MoneyPulse accepts a proposed value only when it can reconcile that value with the OCR source.

Annual revenue, processing volume, years in business, requested funding, contact information, and other fields therefore remain tied to what appears in the source document. Unsupported values are discarded instead of being synthesized.

## Local AI architecture

MoneyPulse supports interchangeable local-model backends:

- Ollama;
- LM Studio;
- llama.cpp-compatible HTTP servers;
- optional in-process Hugging Face Transformers.

The current local default is Qwen3 8B. Provider/model settings are configurable from the desktop application or configuration file. Qwen3 4B is a lower-memory choice, but failed the recorded document-classification smoke check through LM Studio; it is not a verified substitute. See [verification results](VERIFICATION.md).

## Data-quality controls

Before a model-proposed value can propagate through the pipeline, MoneyPulse can:

1. compare the proposed value with OCR source text;
2. enforce a versioned output schema;
3. apply deterministic field/domain rules;
4. record provenance and rejected attempts;
5. expose flagged issues and review state in the desktop UI.

## Interfaces

### Desktop

The PySide6 desktop application supports document selection, batch processing, OCR inspection, extracted-data review, validation results, local-model configuration, CSV export, and output-folder access.

### Headless

The CLI exposes the same extraction and validation pipeline for scripted or server-side use:

```bash
python -m src.cli doctor
python -m src.cli process input --output output
```

## Output

MoneyPulse produces reviewable local artifacts, including structured JSON and CSV summaries. External integrations are optional and separately configurable.

## Privacy model

With a local backend selected, OCR and model inference can remain on the operator's machine or private network. Remote model endpoints require explicit configuration. Real merchant documents, credentials, runtime outputs, and local configuration are intentionally excluded from the repository; demos use synthetic data.

## Technology

Python · PySide6 · Tesseract OCR · pdf2image/Poppler · local LLMs · Ollama · LM Studio · llama.cpp · Hugging Face Transformers · JSON/CSV · REST/SOAP integration adapters · pytest

## Quick evaluation

1. Follow the [README quick start](../README.md#quick-start).
2. Run `python examples/run_synthetic_demo.py` to exercise OCR and source-grounded extraction on generated fictional data.
3. Launch `python main.py` for the desktop workflow.
4. Configure Qwen3 through Ollama or LM Studio for live local-model extraction.

See [Architecture](ARCHITECTURE.md), [Setup](SETUP.md), and [Security](../SECURITY.md) for implementation details.
