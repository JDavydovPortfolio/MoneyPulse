# Setup and troubleshooting

## System tools

Use Python 3.12 or 3.13 and a virtual environment. The current verification host is Linux; Windows/macOS installation steps are provided for users, not claimed as fresh platform certification.

On Debian/Ubuntu:

```bash
sudo apt-get update
sudo apt-get install tesseract-ocr poppler-utils
```

On macOS with Homebrew:

```bash
brew install tesseract poppler
```

On Windows, follow the installers referenced in the upstream [Tesseract installation guide](https://tesseract-ocr.github.io/tessdoc/Installation.html) and [pdf2image installation guide](https://pdf2image.readthedocs.io/en/latest/installation.html). Add the directories containing `tesseract.exe`, `pdfinfo.exe`, and `pdftoppm.exe` to PATH, then open a new terminal. MoneyPulse does not bundle these executables.

Verify in the terminal where you will launch MoneyPulse:

```bash
python --version
tesseract --version
pdfinfo -v
pdftoppm -v
```

English OCR data must be installed. For Linux desktops, Qt may also need your distribution's graphical libraries. Use the offscreen platform only for automated tests; it does not display a desktop window.

## Python environment

From the repository root:

```bash
python -m venv .venv
```

| Shell | Activation |
| --- | --- |
| Linux/macOS Bash | `source .venv/bin/activate` |
| Windows PowerShell | `.\.venv\Scripts\Activate.ps1` |
| Windows Command Prompt | `.venv\Scripts\activate.bat` |

If PowerShell blocks activation, you can call `.\.venv\Scripts\python.exe` directly for each command without changing machine security policy.

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt -c constraints-tested.txt
python -m pip check
```

Use `requirements-core.txt` for headless processing. `constraints-tested.txt` records the tested dependency versions and prevents accidental dependency drift; it is not a universal wheel lock or a guarantee for every OS/interpreter. Optional Transformers, CRM, and binary-build stacks have separate requirements and require separate deployment verification.

## Local models

### Ollama

Install Ollama, start its service, and download the verified model:

```bash
ollama pull gemma4:e2b-it-qat
ollama list
```

Keep MoneyPulse's defaults (`ollama`, `http://localhost:11434`, `gemma4:e2b-it-qat`).

### LM Studio

Download Gemma 4 E2B QAT GGUF; the previous live verification used Q4_0. Load it or enable the server's model-loading behavior, then start its local API server on port 1234. In MoneyPulse, use **Settings → Configuration → Auto-detect Ollama / LM Studio** and save. The app uses the identifier exposed by the server; a GGUF filename is not necessarily that identifier.

The app persists settings in local, git-ignored `config.yaml`. You can also copy `config.example.yaml` to `config.yaml` and edit the documented settings. Invalid settings fail explicitly. The desktop reports a saved-config error before using defaults.

The native LM Studio chat route disables reasoning and storage. Older versions without that route use the OpenAI-compatible fallback; check your server's own logging/storage settings.

## Run and review

```bash
python main.py
```

1. Browse or drop PDF, PNG, JPG, or JPEG files.
2. Process them. Stop requests finish the current document before leaving the batch.
3. Select each document in **Document results**.
4. Compare **OCR Preview** and **Extracted Data** with the original file.
5. Read **Validation Results**, including missing/invalid values and review state.
6. Use **Export CSV Summary** or **Open Output Folder** to inspect local artifacts.

`Present` means a value was extracted; validation details appear in their own tab. A validation pass checks formats, not factual accuracy. The desktop prepares unapproved local output and does not submit to a CRM or offer an external approval workflow.

CSV strings that could be spreadsheet formulas receive a leading apostrophe; JSON retains the original value. Recheck escaping if another application imports and re-exports the CSV.

## Headless processing

With the same saved configuration:

```bash
python -m src.cli doctor
python -m src.cli process input --output output
```

Or provide settings explicitly:

```bash
python -m src.cli process application.pdf --provider lm_studio --host http://localhost:1234 --model YOUR_SERVER_MODEL_ID
```

Directories are scanned non-recursively, in filename order; unsupported files are ignored within directories. Explicit unsupported/missing inputs fail before processing. The CLI performs component checks before extraction and prints a JSON summary without raw OCR text.

Exit codes: `0` means checks passed or all extractions completed and passed domain validation; `1` means a component, document, or domain check failed; `2` means invalid input/configuration or an output/setup error. Review is still required after exit code 0. Processing results and output paths are local; use file permissions appropriate for the documents.

## Common problems

| Symptom | What to check |
| --- | --- |
| Tesseract not found | Verify PATH in the current terminal or set `tesseract_path` in `config.yaml`. |
| Cannot determine PDF page count | Run `pdfinfo -v`; check Poppler PATH and whether the PDF is corrupt or encrypted. Password-protected PDFs are not configured by this app. |
| Provider/model unavailable | Start the API server; verify host/port and the exact model identifier. Auto-detect in the GUI can help. |
| LM Studio works in chat but fails in MoneyPulse | Enable its API server, check the server model ID, and inspect sanitized server errors. |
| Empty or incorrect OCR | Inspect source image quality, orientation, layout, and English OCR data. The app does not guarantee arbitrary layouts or handwriting. |
| Validation failed | Inspect flagged values against the original. Missing optional fields stay empty; malformed values are not silently corrected. |
| No CSV export after selecting new files | Exports belong to the completed batch; process the new selection first. |
| Local output failure | Check output directory permissions and disk space. Processing must not report success when JSON writing fails. |
| Native desktop cannot start | Check PySide6 installation and OS graphical libraries; run from a terminal for the actual error. |

## Release checks

```bash
python scripts/verify.py --fresh
```

The verifier installs the tested dependency constraints in a temporary environment. Optional security database check (requires network):

```bash
python -m pip install pip-audit -c constraints-tested.txt
python -m pip_audit
```

With a live model server, also run `python scripts/verify.py --fresh --live-model ollama` or `--live-model lm_studio`. See [VERIFICATION.md](VERIFICATION.md) for what was actually tested.
