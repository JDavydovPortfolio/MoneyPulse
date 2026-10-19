import pytest

from src.llm import LLMParser
from src.llm_providers import LLMProvider


class FakeProvider(LLMProvider):
    def __init__(self, responder=None):
        super().__init__("fake-model")
        self.prompts = []
        self.responder = responder or (lambda prompt: "Example Value")

    def generate(self, prompt, max_tokens=128, temperature=0.0):
        self.prompts.append(prompt)
        return self.responder(prompt)

    def test_connection(self):
        return True


def test_parser_uses_injected_provider_without_loading_a_model():
    provider = FakeProvider(
        lambda prompt: (
            "Example Merchant LLC"
            if "merchant or business name" in prompt
            else ""
        )
    )
    parser = LLMParser(provider="test", provider_instance=provider)
    result = parser.parse_document("Business Name: Example Merchant LLC", "application.pdf")
    assert result["source_file"] == "application.pdf"
    assert result["llm_provider"] == "test"
    assert result["llm_model"] == "fake-model"
    assert result["merchant_name"] == "Example Merchant LLC"
    assert result["schema_version"] == "1.0"
    assert result["review_state"] == "unreviewed"
    assert result["review_approved"] is False
    assert "confidence_score" not in result
    assert len(provider.prompts) == 14


def test_parser_rejects_empty_document():
    parser = LLMParser(provider="test", provider_instance=FakeProvider())
    with pytest.raises(ValueError, match="empty document"):
        parser.parse_document("   ")


def test_clean_response_preserves_colons_inside_value():
    provider = FakeProvider(
        lambda prompt: (
            "merchant_name: Acme: East"
            if "merchant or business name" in prompt
            else ""
        )
    )
    parser = LLMParser(provider="test", provider_instance=provider)
    result = parser.parse_document("Business Name: Acme: East")
    assert result["merchant_name"] == "Acme: East"


def test_parser_checks_later_chunks_when_field_is_missing_from_first_chunk():
    words = ["filler"] * 512 + [
        "LATER_CHUNK_MARKER",
        "Business",
        "Name",
        "Example",
        "Harbor",
        "LLC",
    ]

    def responder(prompt):
        if "merchant or business name" in prompt and "LATER_CHUNK_MARKER" in prompt:
            return "Example Harbor LLC"
        return "not found"

    provider = FakeProvider(responder)
    parser = LLMParser(provider="test", provider_instance=provider)
    result = parser.parse_document(" ".join(words))
    assert result["merchant_name"] == "Example Harbor LLC"
    assert result["provenance"]["document_chunks"] == 2
    assert len(result["provenance"]["field_attempts"]["merchant_name"]) == 2


def test_parser_records_raw_model_attempts_without_trusting_missing_markers():
    provider = FakeProvider(lambda prompt: "N/A")
    parser = LLMParser(provider="test", provider_instance=provider)
    result = parser.parse_document("Some OCR text")
    assert result["merchant_name"] == ""
    attempts = result["provenance"]["field_attempts"]["merchant_name"]
    assert attempts == [{"chunk_index": 0, "raw_response": "N/A"}]


@pytest.mark.parametrize("text", [
    "Requested Funding Amount: $75000",
    "Business Name: Example LLC. Unrequested funding amount: $75000",
    "Invoice. Business Name: Example LLC. Requested Funding Amount: $75000",
    "Bank statement. Business Name: Example LLC. Requested Funding Amount: $75000",
    "Loan agreement. Business Name: Example LLC. Requested Funding Amount: $75000",
    "Business Name: Example LLC. Requested Funding Amount: $75000 " + "filler " * 512 + "Contract",
])
def test_document_type_fallback_withholds_missing_or_conflicting_evidence(text):
    parser = LLMParser(provider="test", provider_instance=FakeProvider(lambda prompt: "unknown"))
    result = parser.parse_document(text)
    assert result["document_type"] == ""
    assert result["review_approved"] is False
    assert result["flagged_issues"] == []


@pytest.mark.parametrize("source, expected", [
    ("Business Name: Example Harbor Coffee LLC", ""),
    ("Business Name: Example Harbor LLC. Business Type: Coffee Shop", "Coffee Shop"),
])
def test_business_type_requires_a_type_label_not_just_a_matching_company_name(source, expected):
    candidate = "Coffee Shop" if expected else "Coffee LLC"
    provider = FakeProvider(lambda prompt: candidate if "Extract the business type" in prompt else "")
    result = LLMParser(provider="test", provider_instance=provider).parse_document(source)
    assert result["business_info"]["business_type"] == expected
