from src.llm_detector import LLMProviderDetector, RECOMMENDED_MODEL


def _mark_detected(detector, provider_id, host):
    detector.detected_providers[provider_id] = {
        **detector.providers[provider_id],
        "host": host,
    }


def test_detector_builds_pipeline_compatible_config_with_gemma_default():
    detector = LLMProviderDetector()
    _mark_detected(detector, "ollama", "http://localhost:11434")
    detector.available_models["ollama"] = ["mistral:7b", RECOMMENDED_MODEL]
    assert detector.create_config_for_provider("ollama") == {
        "llm_provider": "ollama",
        "llm_host": "http://localhost:11434",
        "model": RECOMMENDED_MODEL,
    }


def test_detector_recognizes_lm_studio_gemma_gguf_name():
    detector = LLMProviderDetector()
    _mark_detected(detector, "lm_studio", "http://localhost:1234")
    detector.available_models["lm_studio"] = [
        "some-other-model",
        "ggml-org/gemma-3n-E2B-it-GGUF",
    ]
    assert detector.get_recommended_model("lm_studio") == "ggml-org/gemma-3n-E2B-it-GGUF"


def test_detector_prefers_provider_with_gemma_over_provider_with_more_models():
    detector = LLMProviderDetector()
    _mark_detected(detector, "ollama", "http://localhost:11434")
    _mark_detected(detector, "lm_studio", "http://localhost:1234")
    detector.available_models["ollama"] = ["model-a", "model-b", "model-c"]
    detector.available_models["lm_studio"] = ["gemma-3n-e2b-it"]
    assert detector.get_recommended_provider() == "lm_studio"


def test_detector_prefers_ollama_when_both_have_recommended_gemma():
    detector = LLMProviderDetector()
    _mark_detected(detector, "ollama", "http://localhost:11434")
    _mark_detected(detector, "lm_studio", "http://localhost:1234")
    detector.available_models["ollama"] = [RECOMMENDED_MODEL]
    detector.available_models["lm_studio"] = ["gemma-3n-e2b-it"]
    assert detector.get_recommended_provider() == "ollama"
