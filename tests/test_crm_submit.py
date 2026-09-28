import json

from src.crm_submit import CRMSubmitter, EnterpriseCRMSubmitter


def validated_document():
    return {
        "schema_version": "1.0",
        "merchant_name": "Example Harbor Coffee LLC",
        "ein_or_ssn": "99-9999999",
        "document_type": "application",
        "address": {"street": "123 Example Ave", "city": "New York", "state": "NY", "zip": "10001"},
        "contact_info": {"phone": "2125550100", "email": "finance@example.com"},
        "business_info": {
            "business_type": "Coffee Shop",
            "annual_revenue": "$525000",
            "years_in_business": "4",
            "processing_volume": "$48000",
        },
        "requested_amount": "$75000",
        "source_file": "synthetic.png",
        "flagged_issues": [],
        "llm_provider": "test",
        "llm_model": "fake-model",
        "review_state": "ready_for_review",
        "review_approved": False,
        "provenance": {
            "source": "ocr",
            "source_file": "synthetic.png",
            "provider": "test",
            "model": "fake-model",
            "document_chunks": 1,
            "field_attempts": {},
        },
        "validation_status": "passed",
        "requires_human_review": False,
        "validation_timestamp": "2026-09-28T00:00:00+00:00",
    }


def test_local_submitter_is_deterministic_and_local_only(tmp_path):
    submitter = CRMSubmitter(str(tmp_path))
    document = validated_document()

    result = submitter.submit_document(document)

    assert result["status"] == "prepared"
    assert result["destination"] == "local_only"
    payload = json.loads((tmp_path / result["json_file"].split("/")[-1]).read_text())
    assert payload["merchant_information"]["name"] == "Example Harbor Coffee LLC"
    assert payload["processing_metadata"]["validation_status"] == "passed"
    assert "provenance" not in payload["processing_metadata"]
    assert "confidence_score" not in payload["processing_metadata"]


def test_local_submitter_blocks_invalid_document_but_keeps_reviewable_artifact(tmp_path):
    submitter = CRMSubmitter(str(tmp_path))
    document = validated_document()
    document["validation_status"] = "failed"
    document["requires_human_review"] = True
    document["review_state"] = "needs_correction"

    result = submitter.submit_document(document)

    assert result["status"] == "blocked"
    assert result["destination"] == "local_only"
    assert result["json_file"]


class FakeConnector:
    def __init__(self):
        self.calls = []

    def submit_financial_document(self, payload):
        self.calls.append(payload)
        return {"status": "success", "record_id": "TEST-1"}


def test_enterprise_submission_requires_explicit_human_approval(tmp_path):
    submitter = EnterpriseCRMSubmitter(str(tmp_path))
    submitter.crm_connector = FakeConnector()
    document = validated_document()

    result = submitter.submit_document(document)

    assert result["enterprise_crm_result"]["status"] == "blocked"
    assert submitter.crm_connector.calls == []


def test_enterprise_submission_uses_validated_payload_after_approval(tmp_path):
    submitter = EnterpriseCRMSubmitter(str(tmp_path))
    submitter.crm_connector = FakeConnector()
    document = validated_document()
    document["review_approved"] = True
    document["review_state"] = "approved"

    result = submitter.submit_document(document)

    assert result["enterprise_crm_result"]["status"] == "success"
    assert len(submitter.crm_connector.calls) == 1
    payload = submitter.crm_connector.calls[0]
    assert payload["merchant_information"]["name"] == "Example Harbor Coffee LLC"
    assert payload["processing_metadata"]["review_approved"] is True
