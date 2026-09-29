# Verification and audit record

Date: **2026-09-29**. Scope: the September 29 hardening changes on top of baseline commit `a023d163c0fc0ece02b758cf2a026f4288c72168`.

This is a tested source baseline. It is not a claim that every operating system, model, financial-document layout, CRM deployment, or packaged binary has been certified.

## Fresh install results

| Check | Result |
| --- | --- |
| Python 3.12.14, Linux x86_64, fresh desktop/development environment | Passed; 91 tests, no skips |
| Python 3.13.15, Linux x86_64, fresh desktop/development environment | Passed; 91 tests, no skips |
| Dependency consistency | `pip check` passed in both fresh environments |
| Source compilation | Passed for main, source, tests, examples, and scripts |
| GUI | Offscreen initialization and synthetic OCR processing passed; batch selection, plain text, worker guards, and saved-setting restart covered |
| OCR | Real generated image and multi-page PDF extraction passed |
| Provider HTTP integration | Temporary local Ollama/LM Studio contract servers passed; these are fixture responses, not model inference |
| Headless CLI | Real OCR/fixture-provider processing, invalid input, corrupt input, and unavailable-provider cases covered |
| Separate core-only install | Demo and CLI help passed; PySide6, Torch, and Zeep absent |
| Bandit 1.9.4 | Passed at medium-or-higher severity (`-ll`) |
| pip-audit 2.10.1 | No known vulnerabilities reported for the installed tested stack after pip was updated to 26.2.1 |
| Git diff whitespace checks | Passed |

Tesseract **5.3.4** and Poppler **26.05.0** were present. `constraints-tested.txt` records the installed package versions; optional Transformers/CRM/build stacks are outside that snapshot's verified scope.

Commands:

```bash
python scripts/verify.py --fresh
python3.13 scripts/verify.py --fresh
python -m pip_audit
```

The fresh gate upgrades pip, installs the declared development/desktop stack with tested constraints in a temporary environment, runs `pip check`, compiles source, executes all tests and the strict synthetic OCR demo, and runs Bandit. Local HTTP tests need permission to bind localhost sockets. A sandbox-blocked socket test was rerun with that permission; it was not skipped or recorded as a pass.

The independent core-only check installed `requirements-core.txt` with the same constraints in another fresh environment, ran `pip check`, CLI help, and the synthetic demo, and confirmed optional desktop/Transformers/SOAP modules were absent.

## Safety regressions

New cases reproduced the prior defects before fixes: spreadsheet formula cells, truthy non-boolean approval, direct connector bypass, transmission after local-output failure, invalid provenance indices/counts, and malformed optional financial/contact values. The final suite also covers multi-page rendering, batch review, configuration persistence/write failure, processing reentry guards, and separate pipeline log destinations.

These tests verify specific behavior, not complete security. Format validation does not prove a value appears in the original document. Human review is required for every model extraction.

## Live-model evidence

The existing September 28 repository record reports real Tesseract-to-Gemma smoke tests through:

- Ollama: Gemma 4 E2B QAT, `gemma4:e2b-it-qat`, 30.41 seconds.
- LM Studio native API: Gemma 4 E2B QAT Q4_0, `gemma-4-e2b-it-qat@q4_0`, 57.71 seconds.

Those runs matched merchant, requested amount, and email, passed deterministic validation, left review unapproved, and kept output local. They are historical smoke-test evidence, not new measurements or accuracy benchmarks. The September 29 verification environment had no live Ollama model available; `doctor` correctly returned a component error and nonzero exit. No live-model pass is claimed for this host.

Repeat the current live smoke test on a machine with the intended model and server before distributing a deployment or changing provider behavior:

```bash
python scripts/verify.py --fresh --live-model ollama
python scripts/verify.py --fresh --live-model lm_studio
```

## Privacy/history audit

The cloned repository exposed one branch (`main`) and **47 reachable commits** before this change. All **243 unique historical blobs** were inspected with targeted credential/path checks; **16 binary blobs** were legacy Python bytecode, whose printable strings were also examined. Current tracked paths were reviewed for documents, credentials, local configuration, generated outputs, and logs.

- No matches were found for the checked GitHub tokens, AWS access-key IDs, OpenAI key formats, or private-key headers; targeted text checks also covered literal credential assignments.
- No real financial documents or runtime output/log artifacts were found in the current tracked tree. The added screenshot uses fictional demo data.
- Old history still contains machine-specific paths, a historical input-directory traceback, build/editor metadata, and Python bytecode. These have been removed from the current tree by earlier maintenance, but are not erased from history. No history rewrite was performed.
- Current configuration, inputs, outputs, logs, and virtual environments remain ignored by git. The example configuration contains no credentials.

This was a targeted review of reachable cloned history, not proof that no secret has ever existed, not a scan of unreachable/deleted server objects, and not a compliance certification. If a real secret is discovered later, rotate it and assess history remediation; deleting it from HEAD is insufficient.

## Remaining deployment limits

- Native Windows/macOS execution and packaged binaries were not freshly tested here. The Qt tests are offscreen Linux tests.
- No representative extraction-accuracy benchmark, handwriting/layout guarantee, or underwriting/compliance claim is made.
- Transformers and deployment-specific external CRM integrations require their own dependencies, credentials, authenticated approval process, and end-to-end validation.
- The desktop/CLI produce local artifacts; they do not offer a production approval audit trail or authenticated CRM submission UI.
- Vulnerability databases change. Re-audit dependencies when updating or preparing a release.
- No GitHub release artifact or external adoption is implied by this source verification record.
