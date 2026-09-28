import copy
import pytest

from src.llm import LLMParser
from src.llm_providers import LLMProvider
from src.schema import SchemaValidationError, validate_extraction_schema


class EmptyProvider(LLMProvider):
    def __init__(self):
        super().__init__("fake")
    def generate(self, prompt, max_tokens=128, temperature=0.0):
        return ""


def valid_schema():
    return LLMParser(provider="test", provider_instance=EmptyProvider()).parse_document("OCR text", "sample.png")


def test_parser_output_satisfies_schema():
    validate_extraction_schema(valid_schema())


def test_schema_rejects_wrong_nested_type():
    data = valid_schema()
    data["address"] = "not-an-object"
    with pytest.raises(SchemaValidationError, match="address must be an object"):
        validate_extraction_schema(data)


def test_schema_rejects_missing_required_key():
    data = valid_schema()
    del data["merchant_name"]
    with pytest.raises(SchemaValidationError, match="missing keys"):
        validate_extraction_schema(data)


def test_schema_rejects_unexpected_root_data():
    data = valid_schema()
    data["approve_funding"] = True
    with pytest.raises(SchemaValidationError, match="unexpected keys"):
        validate_extraction_schema(data)
