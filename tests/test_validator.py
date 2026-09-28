from src.llm import LLMParser
from src.llm_providers import LLMProvider
from src.validator import DocumentValidator


class EmptyProvider(LLMProvider):
    def __init__(self):
        super().__init__("fake")
    def generate(self, prompt, max_tokens=128, temperature=0.0):
        return ""


def valid_document():
    document = LLMParser(provider="test", provider_instance=EmptyProvider()).parse_document("OCR text", "sample.png")
    document.update({
        "merchant_name": "Example Merchant LLC",
        "document_type": "application",
        "ein_or_ssn": "12-3456789",
        "requested_amount": "$25,000",
    })
    document["address"].update({"street": "123 Main St", "city": "New York", "state": "NY", "zip": "10001"})
    document["contact_info"].update({"phone": "(212) 555-0123", "email": "ops@example.com"})
    return document


def test_valid_document_passes_without_fake_confidence():
    result = DocumentValidator().validate_document(valid_document())
    assert result["validation_status"] == "passed"
    assert result["requires_human_review"] is True
    assert result["review_state"] == "ready_for_review"
    assert result["review_approved"] is False
    assert "confidence_score" not in result


def test_invalid_fields_require_review():
    document = valid_document()
    document["ein_or_ssn"] = "123"
    document["address"]["zip"] = "ABC"
    document["contact_info"]["email"] = "not-an-email"
    result = DocumentValidator().validate_document(document)
    assert result["validation_status"] == "failed"
    assert result["requires_human_review"] is True
    assert result["review_state"] == "needs_correction"
    assert len(result["flagged_issues"]) == 3


def test_existing_parser_issue_requires_review_without_faking_domain_failure():
    document = valid_document()
    document["flagged_issues"] = ["Parser returned ambiguous merchant name"]
    result = DocumentValidator().validate_document(document)
    assert result["validation_status"] == "passed"
    assert result["requires_human_review"] is True
    assert result["review_state"] == "needs_review"


def test_amount_validation_rejects_non_numeric_value():
    document = valid_document()
    document["requested_amount"] = "twenty five thousand"
    result = DocumentValidator().validate_document(document)
    assert result["validation_status"] == "failed"
    assert any("Invalid requested amount" in issue for issue in result["flagged_issues"])


def test_missing_optional_tax_id_does_not_invent_or_fail_value():
    document = valid_document()
    document["ein_or_ssn"] = ""
    result = DocumentValidator().validate_document(document)
    assert result["validation_status"] == "passed"
    assert result["ein_or_ssn"] == ""
