from src.llm_detector import LLMProviderDetector, RECOMMENDED_FALLBACK_MODEL, RECOMMENDED_MODEL


def _mark_detected(detector, provider_id, host):
    detector.detected_providers[provider_id] = {
        **detector.providers[provider_id],
        "host": host,
    }


def test_detector_builds_pipeline_compatible_config_with_qwen3_default():
    detector = LLMProviderDetector()
    _mark_detected(detector, "ollama", "http://localhost:11434")
    detector.available_models["ollama"] = ["mistral:7b", RECOMMENDED_MODEL]
    assert detector.create_config_for_provider("ollama") == {
        "llm_provider": "ollama",
        "llm_host": "http://localhost:11434",
        "model": RECOMMENDED_MODEL,
    }


def test_detector_recognizes_lm_studio_qwen3_8b_name():
    detector = LLMProviderDetector()
    _mark_detected(detector, "lm_studio", "http://localhost:1234")
    detector.available_models["lm_studio"] = [
        "some-other-model",
        "Qwen3-8B-Q4_K_M.gguf",
    ]
    assert detector.get_recommended_model("lm_studio") == "Qwen3-8B-Q4_K_M.gguf"


def test_detector_prefers_qwen3_8b_over_qwen3_14b():
    detector = LLMProviderDetector()
    _mark_detected(detector, "lm_studio", "http://localhost:1234")
    detector.available_models["lm_studio"] = [
        "Qwen3-14B-Q4_K_M.gguf",
        "Qwen3-8B-Q4_K_M.gguf",
    ]
    assert detector.get_recommended_model("lm_studio") == "Qwen3-8B-Q4_K_M.gguf"


def test_detector_prefers_provider_with_qwen3_over_provider_with_unranked_models():
    detector = LLMProviderDetector()
    _mark_detected(detector, "ollama", "http://localhost:11434")
    _mark_detected(detector, "lm_studio", "http://localhost:1234")
    detector.available_models["ollama"] = ["model-a", "model-b", "model-c"]
    detector.available_models["lm_studio"] = ["Qwen3-8B-Q4_K_M.gguf"]
    assert detector.get_recommended_provider() == "lm_studio"


def test_detector_prefers_ollama_when_both_have_recommended_qwen3():
    detector = LLMProviderDetector()
    _mark_detected(detector, "ollama", "http://localhost:11434")
    _mark_detected(detector, "lm_studio", "http://localhost:1234")
    detector.available_models["ollama"] = [RECOMMENDED_MODEL]
    detector.available_models["lm_studio"] = ["Qwen3-8B-Q4_K_M.gguf"]
    assert detector.get_recommended_provider() == "ollama"


def test_detector_uses_qwen3_4b_as_low_memory_fallback():
    detector = LLMProviderDetector()
    _mark_detected(detector, "ollama", "http://localhost:11434")
    detector.available_models["ollama"] = ["mistral:7b", RECOMMENDED_FALLBACK_MODEL]
    assert detector.get_recommended_model("ollama") == RECOMMENDED_FALLBACK_MODEL
