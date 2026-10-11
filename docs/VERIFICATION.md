# Verification and audit record

Date: **2026-09-29**, with an incremental hardening update on **2026-10-10/11**. The September 29 scope is the original release-hardening pass on top of baseline commit `a023d163c0fc0ece02b758cf2a026f4288c72168`; later evidence is called out separately below.

This is a tested source baseline. It is not a claim that every operating system, model, financial-document layout, CRM deployment, or packaged binary has been certified.

## October 2026 incremental hardening evidence

The October hardening added deterministic source grounding for model-proposed values, local/private endpoint enforcement by default, OCR input/resource ceilings, and focused regression coverage for those boundaries.

After the grounding/resource-limit changes, the targeted parser/provider/OCR/hardening regression run reported **45 passed** and source compilation passed. That targeted run is evidence for the changed components; it is not being represented as a replacement for the full fresh-environment gate recorded below.

A GitHub-hosted workflow was then prepared to mirror the fresh verifier on Python 3.12/3.13 plus a core-only smoke job. The initial workflow run and one retry were accepted by GitHub Actions, but every job completed without a runner assignment (`runner_id: 0`) and with zero executed steps. No job logs existed because the jobs never started. Therefore **no passing hosted-CI result is claimed**. The workflow is kept manual-only until a GitHub-hosted runner can actually execute it.

The last complete fresh-environment release-gate evidence remains the September 29 record below. Before creating a new release, run the current commit through the checklist in [RELEASE.md](RELEASE.md), including a fresh full verifier run and native target-platform check.

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

September 29 cases reproduced the prior defects before fixes: spreadsheet formula cells, truthy non-boolean approval, direct connector bypass, transmission after local-output failure, invalid provenance indices/counts, and malformed optional financial/contact values. The suite also covers multi-page rendering, batch review, configuration persistence/write failure, processing reentry guards, and separate pipeline log destinations.

The October grounding layer adds a separate boundary: model-proposed values must reconcile with their OCR source chunk before they are propagated. Equivalent financial/contact formatting is normalized for comparison; unsupported guesses are discarded while raw attempts remain in provenance. This reduces plausible-looking hallucination propagation but does not prove OCR correctness or document authenticity. Human review remains required for every model extraction.

These tests verify specific behavior, not complete security.

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

The September 29 cloned repository exposed one branch (`main`) and **47 reachable commits** before that change. All **243 unique historical blobs** were inspected with targeted credential/path checks; **16 binary blobs** were legacy Python bytecode, whose printable strings were also examined. Current tracked paths were reviewed for documents, credentials, local configuration, generated outputs, and logs.

- No matches were found for the checked GitHub tokens, AWS access-key IDs, OpenAI key formats, or private-key headers; targeted text checks also covered literal credential assignments.
- No real financial documents or runtime output/log artifacts were found in the current tracked tree. The added screenshot uses fictional demo data.
- Old history still contains machine-specific paths, a historical input-directory traceback, build/editor metadata, and Python bytecode. These have been removed from the current tree by earlier maintenance, but are not erased from history. No history rewrite was performed.
- Current configuration, inputs, outputs, logs, and virtual environments remain ignored by git. The example configuration contains no credentials.

The October commits reviewed here add source code, tests, documentation, configuration, and workflow files; they do not add merchant/applicant documents or runtime output. This incremental review does **not** claim that every historical blob was re-scanned after September 29. Run the current-tree and newly reachable-history audit in [RELEASE.md](RELEASE.md) before publishing a release.

This was a targeted review of reachable cloned history, not proof that no secret has ever existed, not a scan of unreachable/deleted server objects, and not a compliance certification. If a real secret is discovered later, rotate it and assess history remediation; deleting it from HEAD is insufficient.

## Remaining deployment limits

- Native Windows/macOS execution and packaged binaries were not freshly tested in the recorded Linux verifier. The Qt tests are offscreen Linux tests.
- No representative extraction-accuracy benchmark, handwriting/layout guarantee, or underwriting/compliance claim is made.
- Transformers and deployment-specific external CRM integrations require their own dependencies, credentials, authenticated approval process, and end-to-end validation.
- The desktop/CLI produce local artifacts; they do not offer a production approval audit trail or authenticated CRM submission UI.
- Vulnerability databases change. Re-audit dependencies when updating or preparing a release.
- No GitHub release artifact or external adoption is implied by this source verification record.
