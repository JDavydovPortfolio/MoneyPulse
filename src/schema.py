"""Deterministic schema checks for untrusted model extraction output."""

from typing import Any, Dict

SCHEMA_VERSION = "1.0"


class SchemaValidationError(ValueError):
    """Raised when extracted model data does not match the MoneyPulse schema."""


ROOT_FIELDS = {
    "schema_version",
    "merchant_name",
    "ein_or_ssn",
    "document_type",
    "address",
    "contact_info",
    "business_info",
    "requested_amount",
    "source_file",
    "flagged_issues",
    "llm_provider",
    "llm_model",
    "review_state",
    "review_approved",
    "provenance",
}

NESTED_STRING_FIELDS = {
    "address": {"street", "city", "state", "zip"},
    "contact_info": {"phone", "email"},
    "business_info": {
        "business_type",
        "annual_revenue",
        "years_in_business",
        "processing_volume",
    },
}

ROOT_STRING_FIELDS = {
    "schema_version",
    "merchant_name",
    "ein_or_ssn",
    "document_type",
    "requested_amount",
    "source_file",
    "llm_provider",
    "llm_model",
    "review_state",
}


def _expect_exact_keys(value: Dict[str, Any], expected: set[str], path: str) -> None:
    actual = set(value)
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    problems = []
    if missing:
        problems.append(f"missing keys {missing}")
    if unexpected:
        problems.append(f"unexpected keys {unexpected}")
    if problems:
        raise SchemaValidationError(f"{path}: " + "; ".join(problems))


def validate_extraction_schema(data: Dict[str, Any]) -> None:
    """Validate the parser output shape without inventing or coercing values."""
    if not isinstance(data, dict):
        raise SchemaValidationError("root extraction value must be an object")

    _expect_exact_keys(data, ROOT_FIELDS, "root")

    for field in ROOT_STRING_FIELDS:
        if not isinstance(data[field], str):
            raise SchemaValidationError(f"{field} must be a string")

    if data["schema_version"] != SCHEMA_VERSION:
        raise SchemaValidationError(
            f"unsupported schema_version: {data['schema_version']!r}"
        )

    if not isinstance(data["review_approved"], bool):
        raise SchemaValidationError("review_approved must be a boolean")

    issues = data["flagged_issues"]
    if not isinstance(issues, list) or not all(isinstance(item, str) for item in issues):
        raise SchemaValidationError("flagged_issues must be a list of strings")

    for group, expected_fields in NESTED_STRING_FIELDS.items():
        nested = data[group]
        if not isinstance(nested, dict):
            raise SchemaValidationError(f"{group} must be an object")
        _expect_exact_keys(nested, expected_fields, group)
        for field in expected_fields:
            if not isinstance(nested[field], str):
                raise SchemaValidationError(f"{group}.{field} must be a string")

    provenance = data["provenance"]
    if not isinstance(provenance, dict):
        raise SchemaValidationError("provenance must be an object")

    expected_provenance = {
        "source",
        "source_file",
        "provider",
        "model",
        "document_chunks",
        "field_attempts",
    }
    _expect_exact_keys(provenance, expected_provenance, "provenance")

    for field in ("source", "source_file", "provider", "model"):
        if not isinstance(provenance[field], str):
            raise SchemaValidationError(f"provenance.{field} must be a string")

    if type(provenance["document_chunks"]) is not int or provenance["document_chunks"] < 1:
        raise SchemaValidationError("provenance.document_chunks must be a positive integer")

    attempts = provenance["field_attempts"]
    if not isinstance(attempts, dict):
        raise SchemaValidationError("provenance.field_attempts must be an object")

    for field_name, field_attempts in attempts.items():
        if not isinstance(field_name, str) or not isinstance(field_attempts, list):
            raise SchemaValidationError("provenance.field_attempts entries are malformed")
        for attempt in field_attempts:
            if not isinstance(attempt, dict) or set(attempt) != {"chunk_index", "raw_response"}:
                raise SchemaValidationError(
                    f"provenance.field_attempts.{field_name} entries must contain chunk_index and raw_response"
                )
            if type(attempt["chunk_index"]) is not int or not 0 <= attempt["chunk_index"] < provenance["document_chunks"]:
                raise SchemaValidationError("chunk_index must be an integer within the document chunk range")
            if not isinstance(attempt["raw_response"], str):
                raise SchemaValidationError("raw_response must be a string")
