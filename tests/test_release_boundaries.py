import csv

import pytest

from src.crm_submit import CRMSubmitter, EnterpriseCRMSubmitter, EnterpriseCRMConnector
from src.schema import SchemaValidationError, validate_extraction_schema
from src.validator import DocumentValidator
from test_crm_submit import FakeConnector, validated_document
from test_schema import valid_schema
from test_validator import valid_document


@pytest.mark.parametrize("value", ["=1+1", "+SUM(1,2)", "-1+2", "@SUM(1,2)", "\t=1+1", "  =1+1"])
def test_csv_neutralizes_untrusted_formula_cells(tmp_path, value):
    document = validated_document()
    document["merchant_name"] = value
    document["source_file"] = value
    path = CRMSubmitter(str(tmp_path)).generate_csv_summary([document])
    with open(path, newline="", encoding="utf-8") as handle:
        row = next(csv.DictReader(handle))
    assert row["merchant_name"] == "'" + value
    assert row["source_file"] == "'" + value
    assert document["merchant_name"] == value


@pytest.mark.parametrize("approval", ["false", "true", 1, [True]])
def test_enterprise_rejects_non_boolean_approval(tmp_path, approval):
    submitter = EnterpriseCRMSubmitter(str(tmp_path))
    submitter.crm_connector = FakeConnector()
    document = validated_document()
    document.update(review_approved=approval, review_state="approved")
    assert submitter.submit_document(document)["enterprise_crm_result"]["status"] == "blocked"
    assert not submitter.crm_connector.calls


def test_enterprise_blocks_transmission_when_local_output_fails(tmp_path, monkeypatch):
    submitter = EnterpriseCRMSubmitter(str(tmp_path))
    submitter.crm_connector = FakeConnector()
    document = validated_document()
    document.update(review_approved=True, review_state="approved")
    monkeypatch.setattr(submitter, "_generate_json_file", lambda _: (_ for _ in ()).throw(OSError("disk full")))
    assert submitter.submit_document(document)["enterprise_crm_result"]["status"] == "blocked"
    assert not submitter.crm_connector.calls


def test_direct_connector_cannot_bypass_review_gate():
    connector = EnterpriseCRMConnector({"base_url": "https://crm.example.com", "auth_type": "api_key", "api_key": "fixture"})
    calls = []
    connector._submit_via_rest = lambda payload: calls.append(payload) or {"status": "success"}
    assert connector.submit_financial_document({})["status"] == "blocked"
    assert not calls
    payload = CRMSubmitter()._build_crm_payload(validated_document())
    payload["processing_metadata"].update(review_approved=True, review_state="approved")
    assert connector.submit_financial_document(payload)["status"] == "success"
    assert len(calls) == 1


@pytest.mark.parametrize("field,value", [("document_chunks", True), ("document_chunks", 0)])
def test_schema_rejects_invalid_chunk_count(field, value):
    document = valid_schema()
    document["provenance"][field] = value
    with pytest.raises(SchemaValidationError):
        validate_extraction_schema(document)


@pytest.mark.parametrize("index", [True, -1, 1])
def test_schema_rejects_invalid_chunk_index(index):
    document = valid_schema()
    document["provenance"]["field_attempts"] = {"merchant_name": [{"chunk_index": index, "raw_response": "example"}]}
    with pytest.raises(SchemaValidationError):
        validate_extraction_schema(document)


@pytest.mark.parametrize("field,value", [("ein_or_ssn", "abc123456789"), ("zip", "abc10001"), ("phone", "call2125550100"), ("annual_revenue", "many dollars"), ("years_in_business", "several")])
def test_domain_validation_rejects_junk_inside_optional_values(field, value):
    document = valid_document()
    if field == "zip":
        document["address"][field] = value
    elif field == "phone":
        document["contact_info"][field] = value
    elif field in {"annual_revenue", "years_in_business"}:
        document["business_info"][field] = value
    else:
        document[field] = value
    assert DocumentValidator().validate_document(document)["validation_status"] == "failed"
