#!/usr/bin/env python3
"""Run a deterministic MoneyPulse demo using fictional data and real local OCR."""

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.llm import LLMParser
from src.llm_providers import LLMProvider
from src.pipeline import DocumentPipeline


DEMO_VALUES = {
    "merchant_name": "Example Harbor Coffee LLC",
    "ein_or_ssn": "99-9999999",
    "document_type": "application",
    "requested_amount": "$75000",
    "address_street": "123 Example Avenue",
    "address_city": "New York",
    "address_state": "NY",
    "address_zip": "10001",
    "contact_phone": "2125550100",
    "contact_email": "finance@example.com",
    "business_type": "Coffee Shop",
    "annual_revenue": "$525000",
    "years_in_business": "4",
    "processing_volume": "$48000",
}


class DeterministicDemoProvider(LLMProvider):
    """Fixture provider for verifying the pipeline without a live model server."""

    def __init__(self):
        super().__init__("synthetic-fixture")

    def generate(self, prompt: str, max_tokens: int = 128, temperature: float = 0.0) -> str:
        lower = prompt.lower()
        checks = [
            ("street address", "address_street"),
            ("city name", "address_city"),
            ("state (2-letter", "address_state"),
            ("zip code", "address_zip"),
            ("phone number", "contact_phone"),
            ("email address", "contact_email"),
            ("merchant or business name", "merchant_name"),
            ("tax id", "ein_or_ssn"),
            ("identify the document type", "document_type"),
            ("requested loan or funding amount", "requested_amount"),
            ("business type", "business_type"),
            ("annual revenue amount", "annual_revenue"),
            ("years in business", "years_in_business"),
            ("processing volume", "processing_volume"),
        ]
        for marker, key in checks:
            if marker in lower:
                return DEMO_VALUES[key]
        return ""

    def test_connection(self) -> bool:
        return True


def _load_font(size: int):
    for candidate in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ):
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def make_synthetic_document(path: Path) -> None:
    image = Image.new("RGB", (1900, 760), "white")
    draw = ImageDraw.Draw(image)
    lines = [
        "SYNTHETIC MONEYPULSE DEMO - NOT REAL FINANCIAL DATA",
        "Business Name: Example Harbor Coffee LLC",
        "EIN: 99-9999999",
        "Address: 123 Example Avenue, New York, NY 10001",
        "Phone: 212-555-0100   Email: finance@example.com",
        "Annual Revenue: $525,000",
        "Requested Funding Amount: $75,000",
    ]
    y = 35
    for line in lines:
        draw.text((40, y), line, fill="black", font=_load_font(32))
        y += 95
    image.save(path)


def main() -> int:
    demo_dir = ROOT / "output" / "synthetic_demo"
    demo_dir.mkdir(parents=True, exist_ok=True)
    input_path = demo_dir / "synthetic_merchant_application.png"
    make_synthetic_document(input_path)

    pipeline = DocumentPipeline(
        output_dir=str(demo_dir),
        config={"llm_provider": "ollama", "model": "synthetic-fixture"},
    )
    pipeline.llm = LLMParser(
        provider="synthetic_fixture",
        provider_instance=DeterministicDemoProvider(),
    )

    result = pipeline.process_single_document(str(input_path))
    summary = {
        "processing_status": result.get("processing_status"),
        "validation_status": result.get("validation_status"),
        "review_state": result.get("review_state"),
        "merchant_name": result.get("merchant_name"),
        "source_file": result.get("source_file"),
        "output_result": result.get("output_result"),
    }
    print(json.dumps(summary, indent=2))
    return 0 if result.get("processing_status") == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
