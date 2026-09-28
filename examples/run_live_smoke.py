#!/usr/bin/env python3
"""Exercise a real local provider with fictional OCR input; never substitute a fake."""

import argparse
import json
import re
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from examples.run_synthetic_demo import _load_font
from src.llm_detector import LLMProviderDetector
from src.pipeline import DocumentPipeline


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=("ollama", "lm_studio"), default="ollama")
    parser.add_argument("--model", help="Model identifier; auto-selects the recommended installed model when omitted")
    parser.add_argument("--host", help="Local API endpoint; uses provider default when omitted")
    args = parser.parse_args()

    model = args.model
    if not model:
        detector = LLMProviderDetector()
        provider_info = detector.providers[args.provider].copy()
        provider_info["host"] = (args.host or provider_info["default_host"]).rstrip("/")
        detector.detected_providers[args.provider] = provider_info
        detector.get_available_models(args.provider)
        model = detector.get_recommended_model(args.provider)
        if not model:
            print(json.dumps({
                "passed": False,
                "error": "No installed model could be auto-selected for the configured provider",
                "provider": args.provider,
            }, indent=2))
            return 1

    output = ROOT / "output" / "live_smoke"
    output.mkdir(parents=True, exist_ok=True)
    source = (ROOT / "examples" / "synthetic_merchant_application.txt").read_text()
    lines = source.splitlines()
    image = Image.new("RGB", (2100, 80 + 48 * len(lines)), "white")
    draw = ImageDraw.Draw(image)
    for i, line in enumerate(lines):
        draw.text((35, 30 + i * 48), line, fill="black", font=_load_font(30))
    image_path = output / "synthetic_application.png"
    image.save(image_path)
    pipeline = DocumentPipeline(str(output), {
        "llm_provider": args.provider, "model": model, "llm_host": args.host,
    })
    if not pipeline.llm.test_connection():
        print(json.dumps({"passed": False, "error": "Configured provider/model is unavailable",
                          "provider": args.provider, "model": model}, indent=2))
        return 1
    started = time.monotonic()
    result = pipeline.process_single_document(str(image_path))
    amount = re.sub(r"[$,\s]", "", result.get("requested_amount", ""))
    checks = {
        "processing_completed": result.get("processing_status") == "completed",
        "validation_passed": result.get("validation_status") == "passed",
        "merchant_matches": result.get("merchant_name") == "Example Harbor Coffee LLC",
        "amount_matches": amount in {"75000", "75000.00"},
        "email_matches": result.get("contact_info", {}).get("email") == "finance@example.com",
        "unapproved": result.get("review_approved") is False,
        "local_only": result.get("output_result", {}).get("destination") == "local_only",
    }
    summary = {"provider": args.provider, "model": model,
               "elapsed_seconds": round(time.monotonic() - started, 2),
               "passed": all(checks.values()), "checks": checks,
               "error": result.get("error"), "result": result}
    (output / "result.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "result"}, indent=2))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
