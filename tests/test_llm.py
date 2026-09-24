import pytest

from src.llm import LLMParser
from src.llm_providers import LLMProvider


class FakeProvider(LLMProvider):
    def __init__(self):
        super().__init__("fake-model")
        self.prompts = []

    def generate(
        self,
        prompt,
        max_tokens=128,
        temperature=0.0,
    ):
        self.prompts.append(prompt)
        return "Example Value"

    def test_connection(self):
        return True


def test_parser_uses_injected_provider_without_loading_a_model():
    provider = FakeProvider()
    parser = LLMParser(
        provider="test",
        provider_instance=provider,
    )

    result = parser.parse_document(
        "Business Name: Example Merchant LLC",
        "application.pdf",
    )

    assert (
        result["source_file"]
        == "application.pdf"
    )
    assert result["llm_provider"] == "test"
    assert (
        result["llm_model"]
        == "fake-model"
    )
    assert (
        result["merchant_name"]
        == "Example Value"
    )
    assert len(provider.prompts) == 14


def test_parser_rejects_empty_document():
    parser = LLMParser(
        provider="test",
        provider_instance=FakeProvider(),
    )

    with pytest.raises(
        ValueError,
        match="empty document",
    ):
        parser.parse_document("   ")
