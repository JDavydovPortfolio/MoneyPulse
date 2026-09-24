from src.llm_providers import (
    OllamaProvider,
    OpenAICompatibleProvider,
    create_provider,
)


class FakeResponse:
    def __init__(
        self,
        payload=None,
        status_code=200,
    ):
        self._payload = payload or {}
        self.status_code = status_code

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(
                f"HTTP {self.status_code}"
            )


class FakeSession:
    def __init__(
        self,
        get_payload=None,
        post_payload=None,
    ):
        self.get_payload = get_payload or {}
        self.post_payload = post_payload or {}
        self.last_get = None
        self.last_post = None

    def get(
        self,
        url,
        timeout=None,
    ):
        self.last_get = {
            "url": url,
            "timeout": timeout,
        }
        return FakeResponse(self.get_payload)

    def post(
        self,
        url,
        **kwargs,
    ):
        self.last_post = {
            "url": url,
            **kwargs,
        }
        return FakeResponse(self.post_payload)


def test_ollama_provider_generation():
    session = FakeSession(
        post_payload={
            "response": "  Example Merchant LLC  "
        }
    )
    provider = OllamaProvider(
        "qwen3",
        session=session,
    )

    result = provider.generate(
        "Extract merchant name",
        max_tokens=32,
    )

    assert result == "Example Merchant LLC"
    assert session.last_post["url"].endswith(
        "/api/generate"
    )
    assert (
        session.last_post["json"]["model"]
        == "qwen3"
    )
    assert (
        session.last_post["json"]["stream"]
        is False
    )


def test_openai_compatible_provider_generation():
    session = FakeSession(
        post_payload={
            "choices": [
                {
                    "message": {
                        "content": (
                            "  Example Merchant LLC  "
                        )
                    }
                }
            ]
        }
    )
    provider = OpenAICompatibleProvider(
        "local-model",
        "http://localhost:1234",
        session=session,
    )

    result = provider.generate(
        "Extract merchant name",
        max_tokens=32,
    )

    assert result == "Example Merchant LLC"
    assert session.last_post["url"].endswith(
        "/v1/chat/completions"
    )
    assert (
        session.last_post["json"]["model"]
        == "local-model"
    )


def test_factory_builds_http_providers_without_network_calls():
    session = FakeSession()

    ollama = create_provider(
        "ollama",
        "qwen3",
        session=session,
    )
    lm_studio = create_provider(
        "lm_studio",
        "local-model",
        session=session,
    )
    llama_cpp = create_provider(
        "llama_cpp",
        "local-model",
        session=session,
    )

    assert isinstance(
        ollama,
        OllamaProvider,
    )
    assert isinstance(
        lm_studio,
        OpenAICompatibleProvider,
    )
    assert isinstance(
        llama_cpp,
        OpenAICompatibleProvider,
    )
