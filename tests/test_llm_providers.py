from src.llm_providers import OllamaProvider, OpenAICompatibleProvider, create_provider


class FakeResponse:
    def __init__(self, payload=None, status_code=200, text=""):
        self._payload = payload or {}
        self.status_code = status_code
        self.text = text

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(self, get_payload=None, post_payload=None, get_status=200, post_status=200):
        self.get_payload = get_payload or {}
        self.post_payload = post_payload or {}
        self.get_status = get_status
        self.post_status = post_status
        self.last_get = None
        self.last_post = None

    def get(self, url, timeout=None):
        self.last_get = {"url": url, "timeout": timeout}
        return FakeResponse(self.get_payload, self.get_status)

    def post(self, url, **kwargs):
        self.last_post = {"url": url, **kwargs}
        return FakeResponse(self.post_payload, self.post_status)


def test_ollama_provider_generation():
    session = FakeSession(post_payload={"response": "  Example Merchant LLC  "})
    provider = OllamaProvider("gemma4:e4b", session=session)
    assert provider.generate("Extract merchant name", max_tokens=32) == "Example Merchant LLC"
    assert session.last_post["url"].endswith("/api/generate")
    assert session.last_post["json"]["model"] == "gemma4:e4b"
    assert session.last_post["json"]["think"] is False


def test_openai_compatible_provider_generation():
    session = FakeSession(post_payload={"choices": [{"message": {"content": "  Example Merchant LLC  "}}]})
    provider = OpenAICompatibleProvider("local-model", "http://localhost:1234", session=session)
    assert provider.generate("Extract merchant name", max_tokens=32) == "Example Merchant LLC"
    assert session.last_post["url"].endswith("/v1/chat/completions")


def test_factory_builds_http_providers_without_network_calls():
    session = FakeSession()
    assert isinstance(create_provider("ollama", "gemma4:e4b", session=session), OllamaProvider)
    assert isinstance(create_provider("lm_studio", "local-model", session=session), OpenAICompatibleProvider)
    assert isinstance(create_provider("llama_cpp", "local-model", session=session), OpenAICompatibleProvider)


def test_ollama_connection_checks_configured_model():
    session = FakeSession(get_payload={"models": [{"name": "gemma4:e4b"}]})
    assert OllamaProvider("gemma4:e4b", session=session).test_connection() is True
    assert OllamaProvider("missing-model", session=session).test_connection() is False


def test_openai_compatible_connection_checks_configured_model():
    session = FakeSession(get_payload={"data": [{"id": "local-model"}]})
    assert OpenAICompatibleProvider("local-model", "http://localhost:1234", session=session).test_connection() is True
    assert OpenAICompatibleProvider("missing", "http://localhost:1234", session=session).test_connection() is False

import pytest


def test_ollama_provider_rejects_malformed_response():
    session = FakeSession(post_payload={"unexpected": "value"})
    provider = OllamaProvider("gemma4:e4b", session=session)
    with pytest.raises(ValueError, match="response"):
        provider.generate("Extract merchant name")


def test_openai_compatible_provider_rejects_malformed_response():
    session = FakeSession(post_payload={"choices": []})
    provider = OpenAICompatibleProvider("local-model", "http://localhost:1234", session=session)
    with pytest.raises(ValueError, match="message content"):
        provider.generate("Extract merchant name")


def test_factory_rejects_unknown_provider():
    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        create_provider("not-real", "model")
