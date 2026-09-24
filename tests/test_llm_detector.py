from src.llm_detector import (
    LLMProviderDetector,
)


def test_detector_builds_pipeline_compatible_config():
    detector = LLMProviderDetector()
    detector.detected_providers[
        "ollama"
    ] = {
        **detector.providers["ollama"],
        "host": "http://localhost:11434",
    }
    detector.available_models[
        "ollama"
    ] = ["qwen3:4b"]

    config = (
        detector.create_config_for_provider(
            "ollama"
        )
    )

    assert config == {
        "llm_provider": "ollama",
        "llm_host": "http://localhost:11434",
        "model": "qwen3:4b",
    }
