#!/usr/bin/env python3
"""Cross-platform MoneyPulse release verification.

Use --fresh for the release gate: it creates a temporary virtual environment,
installs requirements-dev.txt, and runs the complete verification suite there.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str], *, env: dict[str, str] | None = None) -> None:
    printable = " ".join(str(part) for part in command)
    print(f"\n> {printable}", flush=True)
    subprocess.run(command, cwd=ROOT, env=env, check=True)


def require_system_tools() -> None:
    missing = [
        name for name in ("tesseract", "pdftoppm", "pdfinfo")
        if shutil.which(name) is None
    ]
    if missing:
        joined = ", ".join(missing)
        raise SystemExit(
            "Missing required system tools: "
            f"{joined}. Install Tesseract OCR and Poppler, then ensure they are on PATH."
        )


def venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def run_live_model_smoke(python: str, live_model: str, env: dict[str, str]) -> None:
    if live_model != "auto":
        run([python, "examples/run_live_smoke.py", "--provider", live_model], env=env)
        return

    last_error: subprocess.CalledProcessError | None = None
    for provider in ("ollama", "lm_studio"):
        try:
            run([python, "examples/run_live_smoke.py", "--provider", provider], env=env)
            return
        except subprocess.CalledProcessError as exc:
            last_error = exc
            print(f"{provider} live smoke did not pass; trying the next local provider.", flush=True)

    if last_error is not None:
        raise last_error
    raise RuntimeError("No live model provider candidates were checked.")


def verify_current_environment(live_model: str | None) -> None:
    require_system_tools()

    if sys.version_info < (3, 12):
        raise SystemExit(
            f"MoneyPulse release verification requires Python 3.12+; found {sys.version.split()[0]}."
        )

    env = os.environ.copy()
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    env.setdefault("PYTHONUNBUFFERED", "1")

    print(f"MoneyPulse verification using Python {sys.version.split()[0]}")
    run([sys.executable, "-m", "compileall", "-q", "main.py", "src", "tests", "examples", "scripts"], env=env)
    run([sys.executable, "-m", "pytest", "-q"], env=env)
    run([sys.executable, "examples/run_synthetic_demo.py"], env=env)
    run([sys.executable, "-m", "bandit", "-q", "-r", "src", "-ll"], env=env)

    if live_model:
        run_live_model_smoke(sys.executable, live_model, env)

    print("\nMoneyPulse local verification passed.", flush=True)


def verify_fresh(live_model: str | None) -> None:
    require_system_tools()

    with tempfile.TemporaryDirectory(prefix="moneypulse-verify-") as temp_dir:
        venv_dir = Path(temp_dir) / ".venv"
        print(f"Creating isolated verification environment at {venv_dir}", flush=True)
        # Invoke venv through the active interpreter. This matches the normal
        # `python -m venv` workflow and supports relocatable builds such as uv's.
        run([sys.executable, "-m", "venv", str(venv_dir)])
        python = venv_python(venv_dir)

        run([str(python), "-m", "pip", "install", "--upgrade", "pip"])
        run([str(python), "-m", "pip", "install", "-r", "requirements-dev.txt", "-c", "constraints-tested.txt"])
        run([str(python), "-m", "pip", "check"])

        command = [str(python), str(Path(__file__).resolve()), "--in-place"]
        if live_model:
            command.extend(["--live-model", live_model])
        run(command)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify MoneyPulse locally.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--fresh",
        action="store_true",
        help="Create a temporary virtualenv, install declared dev/desktop dependencies, and verify there.",
    )
    mode.add_argument("--in-place", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument(
        "--live-model",
        choices=("auto", "ollama", "lm_studio"),
        default=None,
        help="Also run the real Gemma 4 OCR-to-validation smoke test against a local provider.",
    )
    args = parser.parse_args()

    try:
        if args.fresh:
            verify_fresh(args.live_model)
        else:
            verify_current_environment(args.live_model)
    except subprocess.CalledProcessError as exc:
        print(f"\nVerification failed with exit code {exc.returncode}.", file=sys.stderr)
        return exc.returncode or 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
