# Synthetic examples

Everything in this directory is fictional demonstration data. Do not replace these files with real merchant/applicant documents or credentials.

## Deterministic end-to-end demo

`run_synthetic_demo.py` creates a fictional PNG, performs real local Tesseract OCR, uses a deterministic fixture provider instead of a live LLM, passes the extraction through schema/domain validation, and writes local output.

From the repository root:

```bash
python -m pip install -r requirements-core.txt
python examples/run_synthetic_demo.py
```

The fixture provider exists only to make the pipeline reproducible without a model download/server. It does not measure or claim LLM accuracy.

## Text fixture

`synthetic_merchant_application.txt` is a human-readable fictional data fixture useful for parser/test development. The desktop intake path accepts PDF/PNG/JPG/JPEG, not plain text.
