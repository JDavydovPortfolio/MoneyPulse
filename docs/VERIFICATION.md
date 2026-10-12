# Verification and audit record

Date: **2026-10-12** for the v1.0.0 Windows source-release checks, with historical records from **2026-09-29** and **2026-10-10/11** retained below. The September 29 scope is the original release-hardening pass on top of baseline commit `a023d163c0fc0ece02b758cf2a026f4288c72168`.

This is a tested source baseline. It is not a claim that every operating system, model, financial-document layout, CRM deployment, or packaged binary has been certified.

## v1.0.0 Windows source-release evidence - October 12

The source candidate was checked locally on Windows x86_64 (OS build 10.0.26200), PowerShell 7.6.6, with Tesseract 5.4.0.20240606, English OCR data, and Poppler 26.07.0. The first wrapper attempt failed because Tesseract was absent from PATH; the missing system tool was installed and checks were rerun. This infrastructure failure is not recorded as a test pass.

| Check | Observed result |
| --- | --- |
| Python 3.12.13 fresh desktop/development install | Passed; 108 tests, no skips; pip check, compilation, synthetic OCR demo, Bandit |
| Python 3.13.14 fresh desktop/development install | Passed; 108 tests, no skips; pip check, compilation, synthetic OCR demo, Bandit |
| Independent fresh core-only install | pip check, CLI help, real synthetic OCR demo passed; PySide6, Torch, Transformers, Zeep absent |
| Real local-model smoke | LM Studio 0.4.26 at localhost:1234, model identifier gemma-4-e2b-it-qat, locally installed Google Gemma 4 E2B QAT Q4_0 GGUF; all seven smoke checks passed |
| Native Windows desktop | main.py launched; local provider/model settings saved and reloaded by an independently relaunched application; fictional image selected through the native file picker and processed with real OCR/model inference; JSON and CSV export succeeded locally |
| Explicit review boundary | UI showed Ready For Review; generated JSON/CSV retained review_approved false and requires_human_review true; no extraction was approved or sent to a CRM |
| Failure visibility | Unavailable default Ollama provider/model was reported in System Status before selecting the installed LM Studio backend |
| Documentation review | README, setup, architecture, security, changelog, verification, release procedure, and v1.0.0 notes checked against source and observed behavior |

The fresh verifier's GUI tests run offscreen; the separate native workflow above used the displayed Windows application and its actual worker/pipeline, without replacing inference with a fixture. The live backend initially stopped serving after startup; it was restarted, then real smoke processing passed. A single synthetic document is smoke evidence, not an extraction-accuracy or speed benchmark.

These observations precede the final documentation commit. After all release-relevant files are committed, run `.\scripts\release-gate.ps1` again from a clean checkout of the resulting candidate. Its final tagged SHA and fresh gate summary must be recorded in the GitHub Release body, not inserted into the containing tracked commit. Any failing final gate blocks tagging/publication.

### October 12 privacy/history audit

Before the final documentation commit, the current tree had 74 tracked paths. All 306 unique blobs across 68 locally reachable commits were scanned for private-key headers, GitHub/AWS/OpenAI/Google/Slack token formats, JWTs, and literal credential assignments. Relative to the previously recorded audited commit `865bd4e876a2a25a5112c95a2a684f162d2b8879`, this included 20 newly reachable commits and 37 new blobs across local/fetched refs. No matches were found for those checks.

Tracked paths, new-history paths, synthetic examples, and the fictional screenshot were reviewed for real documents, local configuration, and generated runtime artifacts. New history contains source/tests, dependency/workflow configuration, and documentation. The 17 binary blobs include legacy bytecode and the synthetic screenshot; raw binary content was included in the targeted pattern scan. Existing historical machine paths, editor/build metadata, and runtime tracebacks remain as described in the September record; no history rewrite was performed. Local config, synthetic outputs, logs, and virtual environments are ignored and excluded from the release tree.

Repeat the current-tree and new-commit audit after the release documentation commit. The published Release body records that final check. This is a targeted audit of locally reachable history, not proof that secrets have never existed, a scan of unreachable server objects, or a privacy/security/compliance guarantee. No real secret requiring rotation was identified by these checks.

## October 2026 incremental hardening evidence

The October hardening added deterministic source grounding for model-proposed values, local/private endpoint enforcement by default, OCR input/resource ceilings, and focused regression coverage for those boundaries.

After the grounding/resource-limit changes, the targeted parser/provider/OCR/hardening regression run reported **45 passed** and source compilation passed. That targeted run is evidence for the changed components; it is not being represented as a replacement for the full fresh-environment gate recorded below.

A GitHub-hosted workflow was then prepared to mirror the fresh verifier on Python 3.12/3.13 plus a core-only smoke job. The initial workflow run and one retry were accepted by GitHub Actions, but every job completed without a runner assignment (`runner_id: 0`) and with zero executed steps. No job logs existed because the jobs never started. Therefore **no passing hosted-CI result is claimed**. The workflow is kept manual-only until a GitHub-hosted runner can actually execute it.

At the time of that October 10/11 update, the September 29 record below remained the last complete fresh gate. The October 12 Windows record above supersedes that gap. Every release still requires the current committed candidate to pass [RELEASE.md](RELEASE.md).

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

- The historical Linux verifier did not test native Windows/macOS execution. October 12 adds a native Windows source workflow check; native macOS execution and packaged binaries remain outside that scope.
- No representative extraction-accuracy benchmark, handwriting/layout guarantee, or underwriting/compliance claim is made.
- Transformers and deployment-specific external CRM integrations require their own dependencies, credentials, authenticated approval process, and end-to-end validation.
- The desktop/CLI produce local artifacts; they do not offer a production approval audit trail or authenticated CRM submission UI.
- Vulnerability databases change. Re-audit dependencies when updating or preparing a release.
- External adoption is not implied by this source verification record. Published source releases and their exact commits are identified by GitHub Release metadata; packaged binaries require separate verification.
