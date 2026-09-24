from src.validator import DocumentValidator


def valid_document():
    return {
        "merchant_name": "Example Merchant LLC",
        "document_type": "application",
        "ein_or_ssn": "12-3456789",
        "address": {
            "street": "123 Main St",
            "city": "New York",
            "state": "NY",
            "zip": "10001",
        },
        "contact_info": {
            "phone": "(212) 555-0123",
            "email": "ops@example.com",
        },
        "requested_amount": "$25,000",
        "flagged_issues": [],
        "confidence_score": 0.9,
    }


def test_valid_document_passes():
    result = DocumentValidator().validate_document(valid_document())
    assert result["validation_status"] == "passed"
    assert result["requires_human_review"] is False
    assert result["flagged_issues"] == []


def test_invalid_fields_require_review_and_reduce_confidence():
    document = valid_document()
    document["ein_or_ssn"] = "123"
    document["address"]["zip"] = "ABC"
    document["contact_info"]["email"] = "not-an-email"

    result = DocumentValidator().validate_document(document)

    assert result["validation_status"] == "failed"
    assert result["requires_human_review"] is True
    assert len(result["flagged_issues"]) == 3
    assert result["confidence_score"] < 0.9


def test_existing_parser_issue_still_requires_human_review():
    document = valid_document()
    document["flagged_issues"] = ["Parser could not confidently extract owner name"]

    result = DocumentValidator().validate_document(document)

    assert result["validation_status"] == "passed"
    assert result["requires_human_review"] is True
    assert "Parser could not confidently extract owner name" in result["flagged_issues"]


def test_amount_validation_rejects_non_numeric_value():
    document = valid_document()
    document["requested_amount"] = "twenty five thousand"

    result = DocumentValidator().validate_document(document)

    assert result["validation_status"] == "failed"
    assert any("Invalid requested amount" in issue for issue in result["flagged_issues"])
