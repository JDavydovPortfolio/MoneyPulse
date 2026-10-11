import pytest
from PIL import Image

from src.config import validate_config
from src.llm import LLMParser
from src.llm_providers import LLMProvider, create_provider
from src.ocr import OCRProcessor


class MappingProvider(LLMProvider):
    def __init__(self, values):
        super().__init__("fixture")
        self.values = values

    def generate(self, prompt, max_tokens=128, temperature=0.0):
        checks = [
            ("merchant or business name", "merchant_name"),
            ("tax id", "ein_or_ssn"),
            ("identify the document type", "document_type"),
            ("requested loan or funding amount", "requested_amount"),
            ("street address", "address_street"),
            ("city name", "address_city"),
            ("state (2-letter", "address_state"),
            ("zip code", "address_zip"),
            ("phone number", "contact_phone"),
            ("email address", "contact_email"),
            ("business type", "business_type"),
            ("annual revenue amount", "annual_revenue"),
            ("years in business", "years_in_business"),
            ("processing volume", "processing_volume"),
        ]
        lower = prompt.lower()
        for needle, field in checks:
            if needle in lower:
                return self.values.get(field, "")
        return ""


def application_text():
    return (
        "Business Name: Real Merchant LLC\n"
        "EIN: 99-9999999\n"
        "Address: 123 Example Avenue, New York, NY 10001\n"
        "Phone: 212-555-0100 Email: finance@example.com\n"
        "Requested Funding Amount: $75,000"
    )


def parser(values):
    return LLMParser(provider="test", provider_instance=MappingProvider(values))


def test_ungrounded_model_value_is_discarded_but_provenance_is_preserved():
    result = parser({
        "merchant_name": "Invented Merchant LLC",
        "document_type": "application",
    }).parse_document(application_text(), "fixture.png")

    assert result["merchant_name"] == ""
    assert result["document_type"] == "application"
    attempts = result["provenance"]["field_attempts"]["merchant_name"]
    assert attempts[0]["raw_response"] == "Invented Merchant LLC"


def test_grounding_accepts_equivalent_financial_and_contact_formatting():
    result = parser({
        "merchant_name": "Real Merchant LLC",
        "document_type": "application",
        "requested_amount": "$75000",
        "ein_or_ssn": "999999999",
        "contact_phone": "2125550100",
        "address_zip": "10001",
        "contact_email": "FINANCE@example.com",
    }).parse_document(application_text())

    assert result["merchant_name"] == "Real Merchant LLC"
    assert result["requested_amount"] == "$75000"
    assert result["ein_or_ssn"] == "999999999"
    assert result["contact_info"]["phone"] == "2125550100"
    assert result["address"]["zip"] == "10001"
    assert result["contact_info"]["email"] == "FINANCE@example.com"


def test_ungrounded_optional_amount_is_not_propagated():
    result = parser({
        "merchant_name": "Real Merchant LLC",
        "document_type": "application",
        "annual_revenue": "$525000",
    }).parse_document(application_text())
    assert result["business_info"]["annual_revenue"] == ""


def test_remote_model_host_requires_explicit_opt_in():
    with pytest.raises(ValueError, match="Remote model endpoints are disabled"):
        create_provider("ollama", "fixture", host="https://models.example.com")

    provider = create_provider(
        "ollama",
        "fixture",
        host="https://models.example.com",
        allow_remote_host=True,
    )
    assert provider.host == "https://models.example.com"


@pytest.mark.parametrize(
    "host",
    [
        "http://localhost:11434",
        "http://127.0.0.1:11434",
        "http://[::1]:11434",
        "http://192.168.1.5:11434",
        "http://10.0.0.5:11434",
    ],
)
def test_explicit_local_model_hosts_are_allowed(host):
    assert create_provider("ollama", "fixture", host=host).host == host


def test_config_requires_boolean_remote_opt_in():
    with pytest.raises(ValueError, match="Remote model endpoints are disabled"):
        validate_config({"llm_host": "https://models.example.com"})
    with pytest.raises(ValueError, match="must be a boolean"):
        validate_config({
            "llm_host": "https://models.example.com",
            "allow_remote_llm": "true",
        })
    assert validate_config({
        "llm_host": "https://models.example.com",
        "allow_remote_llm": True,
    })["allow_remote_llm"] is True


@pytest.mark.parametrize(
    "field,value",
    [
        ("ocr_max_file_mb", 0),
        ("ocr_max_pdf_pages", -1),
        ("ocr_max_image_pixels", True),
        ("ocr_max_image_pixels", "100"),
    ],
)
def test_config_rejects_invalid_ocr_limits(field, value):
    with pytest.raises(ValueError, match="positive integer"):
        validate_config({field: value})


def test_ocr_rejects_file_above_size_limit_before_decode(tmp_path):
    path = tmp_path / "oversized.png"
    path.write_bytes(b"x" * (1024 * 1024 + 1))
    with pytest.raises(ValueError, match="file size"):
        OCRProcessor(max_file_size_mb=1).extract_text(str(path))


def test_ocr_rejects_pdf_over_page_limit_before_render(tmp_path, monkeypatch):
    import src.ocr as ocr

    path = tmp_path / "many-pages.pdf"
    path.write_bytes(b"%PDF-fixture")
    monkeypatch.setattr(ocr, "pdfinfo_from_path", lambda *args, **kwargs: {"Pages": 3})
    monkeypatch.setattr(
        ocr,
        "convert_from_path",
        lambda *args, **kwargs: pytest.fail("PDF rendering must not start"),
    )

    with pytest.raises(ValueError, match="page count"):
        OCRProcessor(max_pdf_pages=2).extract_text(str(path))


def test_ocr_rejects_image_over_pixel_limit_before_opencv_decode(tmp_path, monkeypatch):
    import src.ocr as ocr

    path = tmp_path / "large.png"
    Image.new("RGB", (20, 20), "white").save(path)
    monkeypatch.setattr(
        ocr.cv2,
        "imread",
        lambda *args, **kwargs: pytest.fail("OpenCV decode must not start"),
    )

    with pytest.raises(ValueError, match="pixel limit"):
        OCRProcessor(max_image_pixels=100).extract_text(str(path))
