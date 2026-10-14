# MoneyPulse project brief

## Overview

MoneyPulse is a local-first AI document-intelligence pipeline for Merchant Cash Advance underwriting and operations. It converts merchant applications and supporting financial documents into structured, validated underwriting data that can be reviewed locally or passed into downstream workflows.

The project combines OCR, configurable local LLM inference, source-grounded extraction, deterministic schema/domain validation, underwriting pre-screen signals, desktop/headless workflows, and optional CRM integration.

## Problem

MCA teams routinely receive merchant information in PDFs, scans, images, applications, and supporting financial documents. Before an underwriter can evaluate a file, that information often has to be read, re-keyed, normalized, and checked manually.

MoneyPulse automates that intake layer while keeping the underlying source visible and the rules inspectable.

## Core workflow

```text
merchant documents
  -> OCR
  -> local AI extraction
  -> source grounding
  -> schema + domain validation
  -> underwriting metrics
  -> optional deterministic pre-screen policy
  -> analyst / underwriter review
  -> local JSON / CSV
  -> optional CRM workflow
```

## Underwriting support

MoneyPulse calculates structured pre-underwriting signals from validated merchant data, including:

- requested funding amount;
- annual revenue;
- processing volume;
- years in business;
- requested amount relative to annual revenue;
- requested amount relative to processing volume.

Operators can optionally configure deterministic business-policy thresholds for those signals. When policy rules are present, MoneyPulse returns an auditable pre-screen recommendation of `advance`, `manual_review`, or `needs_more_data`, together with each rule's input, threshold, and result.

The policy engine is deliberately separate from the LLM so underwriting rules are not improvised by model output.

## Local AI architecture

MoneyPulse supports interchangeable local-model backends:

- Ollama;
- LM Studio;
- llama.cpp-compatible HTTP servers;
- optional in-process Hugging Face Transformers.

The current local default is Qwen3 8B, with Qwen3 4B as a lower-memory alternative. Provider/model settings are configurable from the desktop application or configuration file.

## Data-quality controls

Model output is treated as proposed data rather than unquestioned truth. Before a value can propagate through the pipeline, MoneyPulse can:

1. compare the proposed value with OCR source text;
2. enforce a versioned output schema;
3. apply deterministic field/domain rules;
4. record provenance and rejected attempts;
5. expose flagged issues and review state in the desktop UI.

This architecture is designed to make automated extraction useful in a financial workflow without hiding where values came from.

## Interfaces

### Desktop

The PySide6 desktop application supports document selection, batch processing, OCR inspection, extracted-data review, underwriting signals, validation results, local-model configuration, underwriting-policy configuration, CSV export, and output-folder access.

### Headless

The CLI exposes the same processing pipeline for scripted or server-side use:

```bash
python -m src.cli doctor
python -m src.cli process input --output output
```

## Output

MoneyPulse produces reviewable local artifacts, including structured JSON and CSV summaries. Underwriting pre-screen results are included in the local JSON output. External integrations are optional and separately configurable.

## Privacy model

With a local backend selected, OCR and model inference can remain on the operator's machine or private network. Remote model endpoints require explicit configuration. Real merchant documents, credentials, runtime outputs, and local configuration are intentionally excluded from the repository; demos use synthetic data.

## Technology

Python · PySide6 · Tesseract OCR · pdf2image/Poppler · local LLMs · Ollama · LM Studio · llama.cpp · Hugging Face Transformers · JSON/CSV · REST/SOAP integration adapters · pytest

## Quick evaluation

1. Follow the [README quick start](../README.md#try-it-in-a-few-minutes).
2. Run `python examples/run_synthetic_demo.py` to exercise OCR and the processing pipeline on generated fictional data.
3. Launch `python main.py` for the desktop workflow.
4. Configure Qwen3 through Ollama or LM Studio for live local-model extraction.
5. Add optional underwriting policy thresholds in the desktop Configuration dialog to exercise deterministic pre-screen rules.

See [Architecture](ARCHITECTURE.md), [Setup](SETUP.md), and [Security](../SECURITY.md) for implementation details.
