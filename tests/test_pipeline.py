from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from src.llm import LLMParser
from src.llm_providers import LLMProvider
from src.pipeline import DocumentPipeline


FIELD_VALUES = {
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


class DeterministicProvider(LLMProvider):
    def __init__(self):
        super().__init__("deterministic-fixture")

    def generate(self, prompt, max_tokens=128, temperature=0.0):
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
        for needle, key in checks:
            if needle in lower:
                return FIELD_VALUES[key]
        return ""

    def test_connection(self):
        return True


def _font(size=34):
    for candidate in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def _synthetic_image(path):
    image = Image.new("RGB", (1900, 700), "white")
    draw = ImageDraw.Draw(image)
    lines = [
        "SYNTHETIC MONEY PULSE DEMO",
        "Business Name: Example Harbor Coffee LLC",
        "EIN: 99-9999999",
        "Address: 123 Example Avenue, New York, NY 10001",
        "Phone: 212-555-0100 Email: finance@example.com",
        "Requested Funding Amount: $75,000",
    ]
    y = 40
    for line in lines:
        draw.text((40, y), line, fill="black", font=_font())
        y += 95
    image.save(path)


def _pipeline(tmp_path):
    pipeline = DocumentPipeline(
        output_dir=str(tmp_path / "output"),
        config={"llm_provider": "ollama", "model": "fixture"},
    )
    pipeline.llm = LLMParser(
        provider="test",
        provider_instance=DeterministicProvider(),
    )
    return pipeline


def test_synthetic_ocr_to_validated_local_output_end_to_end(tmp_path):
    image_path = tmp_path / "synthetic.png"
    _synthetic_image(image_path)
    pipeline = _pipeline(tmp_path)

    result = pipeline.process_single_document(str(image_path))

    assert result["processing_status"] == "completed"
    assert "example harbor coffee" in result["extracted_text"].lower()
    assert result["schema_version"] == "1.0"
    assert result["merchant_name"] == "Example Harbor Coffee LLC"
    assert result["validation_status"] == "passed"
    assert result["review_state"] == "ready_for_review"
    assert result["review_approved"] is False
    assert result["output_result"]["status"] == "prepared"
    assert result["output_result"]["destination"] == "local_only"
    assert result["processing_timestamp"]
    output_json = Path(result["output_result"]["json_file"])
    assert result["processing_timestamp"] in output_json.read_text(encoding="utf-8")
    assert "confidence_score" not in result


def test_pipeline_fails_safely_on_malformed_provider_output(tmp_path):
    image_path = tmp_path / "synthetic.png"
    _synthetic_image(image_path)
    pipeline = _pipeline(tmp_path)

    original = pipeline.llm.parse_document
    pipeline.llm.parse_document = lambda text, filename=None: {"merchant_name": "oops"}
    result = pipeline.process_single_document(str(image_path))
    pipeline.llm.parse_document = original

    assert result["processing_status"] == "failed"
    assert "schema" in result["error"].lower() or "missing" in result["error"].lower()


def test_pipeline_rejects_unsupported_input_before_ocr(tmp_path):
    path = tmp_path / "synthetic.txt"
    path.write_text("synthetic", encoding="utf-8")
    result = _pipeline(tmp_path).process_single_document(str(path))
    assert result["processing_status"] == "failed"
    assert "Unsupported file type" in result["error"]
