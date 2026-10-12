# MoneyPulse v1.0.0 release notes (draft)

> Draft only. Do not publish this as a GitHub Release until the exact release-candidate commit has completed the repository-local release gate and the manual checks in `docs/RELEASE.md`.

MoneyPulse v1.0.0 is the first formal GitHub release of the modernized local-first financial-document processing pipeline.

## Highlights

- Local-first OCR and model-assisted extraction for financial-document workflows.
- Provider abstraction for Ollama, LM Studio, llama.cpp-compatible servers, and optional Transformers.
- Source-grounded extraction: model-proposed values must reconcile with the OCR source before they can propagate.
- Versioned extraction schema plus deterministic structural and domain validation.
- Explicit human-review states before downstream use; optional external CRM transmission remains separately gated.
- Local JSON and spreadsheet-safe CSV output.
- Desktop and headless CLI workflows.
- Real-Tesseract synthetic demos that require no private financial documents and no model download.
- Configurable OCR file/page/pixel limits and bounded PDF rendering.
- Local/private model endpoints by default, with deliberate opt-in required for remote model endpoints.

## Verification model

The canonical release gate is repository-local, not GitHub Actions. Hosted Actions are supplemental evidence only and are not a prerequisite to release.

Before publishing v1.0.0, the exact release-candidate commit must complete:

1. Fresh verification under Python 3.12.
2. Fresh verification under Python 3.13.
3. A real local-model smoke test through the intended backend.
4. Native desktop launch and fictional-document processing on the target OS.
5. Current-tree and newly reachable-history privacy/secret review.
6. Documentation and release-note consistency review.

See `docs/RELEASE.md` and `docs/VERIFICATION.md` for the evidence standard and recorded limits.

## Important limits

- MoneyPulse is experimental software, not an underwriting engine or compliance certification system.
- Extracted values require human review.
- Extraction quality depends on OCR quality, document layout, prompts, and the selected model.
- No fixed extraction-accuracy or speed benchmark is claimed.
- External CRM integrations require deployment-specific credentials, approval controls, and testing.
- Packaged binary artifacts should only be attached after separate target-platform build and smoke testing.

## Upgrade / installation

Use Python 3.12 or 3.13 with Tesseract OCR and Poppler installed.

For the deterministic synthetic demo:

```bash
git clone https://github.com/JDavydPortfolio/MoneyPulse.git
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

## Release-candidate commit

TBD after the final release gate. Do not substitute a different commit after verification without rerunning the gate.
