"""Provider abstractions for local MoneyPulse model inference."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Common interface for local text-generation backends."""

    def __init__(self, model: str):
        self.model = model

    @abstractmethod
    def generate(
        self,
        prompt: str,
        max_tokens: int = 128,
        temperature: float = 0.0,
    ) -> str:
        """Generate text for a prompt."""

    def test_connection(self) -> bool:
        """Return whether the provider is ready to accept generation requests."""
        try:
            self.generate("Reply with OK.", max_tokens=8, temperature=0.0)
            return True
        except Exception as exc:
            logger.debug("Provider connection test failed: %s", exc)
            return False


class TransformersProvider(LLMProvider):
    """In-process Hugging Face Transformers backend."""

    MODEL_ALIASES = {
        "phi": "microsoft/phi-2",
    }

    def __init__(self, model: str = "microsoft/phi-2"):
        resolved_model = self.MODEL_ALIASES.get(model, model)
        super().__init__(resolved_model)

        try:
            import torch
            from transformers import pipeline
        except ImportError as exc:
            raise RuntimeError(
                "Transformers provider requires torch and transformers."
            ) from exc

        device = 0 if torch.cuda.is_available() else -1
        self._generator = pipeline(
            "text-generation",
            model=self.model,
            device=device,
        )

    def generate(
        self,
        prompt: str,
        max_tokens: int = 128,
        temperature: float = 0.0,
    ) -> str:
        kwargs: Dict[str, Any] = {
            "max_new_tokens": max_tokens,
            "num_return_sequences": 1,
            "do_sample": temperature > 0,
        }
        if temperature > 0:
            kwargs["temperature"] = temperature

        response = self._generator(prompt, **kwargs)
        if not response:
            return ""

        first = response[0]
        generated = (
            first.get("generated_text", "")
            if isinstance(first, dict)
            else str(first)
        )
        if generated.startswith(prompt):
            generated = generated[len(prompt):]
        return generated.strip()

    def test_connection(self) -> bool:
        return self._generator is not None


class OllamaProvider(LLMProvider):
    """Ollama HTTP backend."""

    def __init__(
        self,
        model: str,
        host: str = "http://localhost:11434",
        session: Optional[requests.Session] = None,
    ):
        super().__init__(model)
        self.host = host.rstrip("/")
        self.session = session or requests.Session()

    def generate(
        self,
        prompt: str,
        max_tokens: int = 128,
        temperature: float = 0.0,
    ) -> str:
        response = self.session.post(
            f"{self.host}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            },
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        text = data.get("response")
        if text is None:
            raise ValueError(
                "Ollama response did not include a 'response' field"
            )
        return str(text).strip()

    def test_connection(self) -> bool:
        try:
            response = self.session.get(
                f"{self.host}/api/tags",
                timeout=5,
            )
            return response.status_code == 200
        except requests.RequestException:
            return False


class OpenAICompatibleProvider(LLMProvider):
    """Local OpenAI-compatible HTTP backend used by LM Studio and llama.cpp."""

    def __init__(
        self,
        model: str,
        host: str,
        session: Optional[requests.Session] = None,
    ):
        super().__init__(model)
        self.host = host.rstrip("/")
        self.session = session or requests.Session()

    def generate(
        self,
        prompt: str,
        max_tokens: int = 128,
        temperature: float = 0.0,
    ) -> str:
        response = self.session.post(
            f"{self.host}/v1/chat/completions",
            json={
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False,
            },
            headers={"Content-Type": "application/json"},
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError(
                "OpenAI-compatible response did not include message content"
            ) from exc
        return str(content).strip()

    def test_connection(self) -> bool:
        try:
            response = self.session.get(
                f"{self.host}/v1/models",
                timeout=5,
            )
            return response.status_code == 200
        except requests.RequestException:
            return False


DEFAULT_HOSTS = {
    "ollama": "http://localhost:11434",
    "lm_studio": "http://localhost:1234",
    "lm_studio_ci": "http://localhost:1234",
    "llama_cpp": "http://localhost:8080",
}


def create_provider(
    provider_id: str,
    model: str,
    host: Optional[str] = None,
    session: Optional[requests.Session] = None,
) -> LLMProvider:
    """Build a provider from MoneyPulse configuration."""
    normalized = (
        provider_id or "transformers"
    ).strip().lower()

    if normalized in {
        "transformers",
        "huggingface",
        "local_transformers",
    }:
        return TransformersProvider(model=model)

    if normalized == "ollama":
        return OllamaProvider(
            model=model,
            host=host or DEFAULT_HOSTS["ollama"],
            session=session,
        )

    if normalized in {
        "lm_studio",
        "lm_studio_ci",
        "llama_cpp",
    }:
        return OpenAICompatibleProvider(
            model=model,
            host=host or DEFAULT_HOSTS[normalized],
            session=session,
        )

    raise ValueError(
        f"Unsupported LLM provider: {provider_id}"
    )
