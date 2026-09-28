from src.llm_providers import LMStudioProvider, OllamaProvider, OpenAICompatibleProvider, create_provider


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
    provider = OllamaProvider("gemma4:e2b-it-qat", session=session)
    assert provider.generate("Extract merchant name", max_tokens=32) == "Example Merchant LLC"
    assert session.last_post["url"].endswith("/api/generate")
    assert session.last_post["json"]["model"] == "gemma4:e2b-it-qat"
    assert session.last_post["json"]["think"] is False


def test_openai_compatible_provider_generation():
    session = FakeSession(post_payload={"choices": [{"message": {"content": "  Example Merchant LLC  "}}]})
    provider = OpenAICompatibleProvider("local-model", "http://localhost:1234", session=session)
    assert provider.generate("Extract merchant name", max_tokens=32) == "Example Merchant LLC"
    assert session.last_post["url"].endswith("/v1/chat/completions")


def test_lm_studio_provider_disables_reasoning_and_reads_native_message_output():
    session = FakeSession(post_payload={"output": [
        {"type": "reasoning", "content": "hidden reasoning"},
        {"type": "message", "content": "Example Merchant LLC"},
    ]})
    provider = LMStudioProvider("local-model", "http://localhost:1234", session=session)

    assert provider.generate("Extract merchant", max_tokens=32) == "Example Merchant LLC"
    assert session.last_post["url"].endswith("/api/v1/chat")
    assert session.last_post["json"]["reasoning"] == "off"
    assert session.last_post["json"]["max_output_tokens"] == 32
    assert session.last_post["json"]["store"] is False


def test_lm_studio_provider_falls_back_when_native_api_is_unavailable():
    class LegacyLMStudioSession(FakeSession):
        def __init__(self):
            super().__init__()
            self.posts = []

        def post(self, url, **kwargs):
            self.posts.append({"url": url, **kwargs})
            if url.endswith("/api/v1/chat"):
                return FakeResponse(status_code=404)
            return FakeResponse({"choices": [{"message": {"content": "Legacy response"}}]})

    session = LegacyLMStudioSession()
    provider = LMStudioProvider("local-model", "http://localhost:1234", session=session)

    assert provider.generate("Extract merchant") == "Legacy response"
    assert [post["url"].rsplit("/", 1)[-1] for post in session.posts] == ["chat", "completions"]


def test_factory_builds_http_providers_without_network_calls():
    session = FakeSession()
    assert isinstance(create_provider("ollama", "gemma4:e2b-it-qat", session=session), OllamaProvider)
    assert isinstance(create_provider("lm_studio", "local-model", session=session), LMStudioProvider)
    assert isinstance(create_provider("llama_cpp", "local-model", session=session), OpenAICompatibleProvider)


def test_ollama_connection_checks_configured_model():
    session = FakeSession(get_payload={"models": [{"name": "gemma4:e2b-it-qat"}]})
    assert OllamaProvider("gemma4:e2b-it-qat", session=session).test_connection() is True
    assert OllamaProvider("missing-model", session=session).test_connection() is False


def test_openai_compatible_connection_checks_configured_model():
    session = FakeSession(get_payload={"data": [{"id": "local-model"}]})
    assert OpenAICompatibleProvider("local-model", "http://localhost:1234", session=session).test_connection() is True
    assert OpenAICompatibleProvider("missing", "http://localhost:1234", session=session).test_connection() is False

import pytest


def test_ollama_provider_rejects_malformed_response():
    session = FakeSession(post_payload={"unexpected": "value"})
    provider = OllamaProvider("gemma4:e2b-it-qat", session=session)
    with pytest.raises(ValueError, match="response"):
        provider.generate("Extract merchant name")


def test_openai_compatible_provider_rejects_malformed_response():
    session = FakeSession(post_payload={"choices": []})
    provider = OpenAICompatibleProvider("local-model", "http://localhost:1234", session=session)
    with pytest.raises(ValueError, match="message content"):
        provider.generate("Extract merchant name")


def test_lm_studio_provider_rejects_malformed_native_response():
    provider = LMStudioProvider("local-model", "http://localhost:1234", session=FakeSession(
        post_payload={"output": [{"type": "reasoning", "content": "thinking"}]}
    ))
    with pytest.raises(ValueError, match="message content"):
        provider.generate("Extract merchant name")


def test_factory_rejects_unknown_provider():
    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        create_provider("not-real", "model")


@pytest.mark.parametrize("content", [{"name": "invented"}, ["invented"], 123, True])
def test_http_providers_reject_non_text_generation(content):
    ollama = OllamaProvider("fixture", session=FakeSession(post_payload={"response": content}))
    studio = OpenAICompatibleProvider("fixture", "http://localhost:1234", session=FakeSession(
        post_payload={"choices": [{"message": {"content": content}}]}))
    for provider in (ollama, studio):
        with pytest.raises(ValueError, match="text"):
            provider.generate("Extract name")
