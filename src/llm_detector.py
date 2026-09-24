#!/usr/bin/env python3
"""Detection and configuration helpers for local LLM providers."""

import logging
from typing import Dict, List, Optional

import requests
import yaml

from .llm_providers import DEFAULT_HOSTS, create_provider

logger = logging.getLogger(__name__)


class LLMProviderDetector:
    """Detect locally running model servers and available models."""

    def __init__(self):
        self.providers = {
            "ollama": {
                "name": "Ollama",
                "default_host": DEFAULT_HOSTS["ollama"],
                "models_endpoint": "/api/tags",
                "icon": "🐙",
            },
            "lm_studio": {
                "name": "LM Studio",
                "default_host": DEFAULT_HOSTS["lm_studio"],
                "models_endpoint": "/v1/models",
                "icon": "🎯",
            },
            "lm_studio_ci": {
                "name": "LM Studio CI",
                "default_host": DEFAULT_HOSTS["lm_studio_ci"],
                "models_endpoint": "/v1/models",
                "icon": "🚀",
            },
            "llama_cpp": {
                "name": "llama.cpp",
                "default_host": DEFAULT_HOSTS["llama_cpp"],
                "models_endpoint": "/v1/models",
                "icon": "🦙",
            },
        }

        self.detected_providers: Dict[str, Dict] = {}
        self.available_models: Dict[str, List[str]] = {}

    def detect_all_providers(self) -> Dict[str, Dict]:
        logger.info(
            "Detecting available local LLM providers"
        )
        self.detected_providers = {}

        for provider_id, provider_info in (
            self.providers.items()
        ):
            host = provider_info["default_host"]
            try:
                provider = create_provider(
                    provider_id=provider_id,
                    model="__probe__",
                    host=host,
                )
                if provider.test_connection():
                    detected = provider_info.copy()
                    detected["host"] = host
                    detected["status"] = "available"
                    self.detected_providers[
                        provider_id
                    ] = detected
                    logger.info(
                        "Detected %s at %s",
                        provider_info["name"],
                        host,
                    )
            except Exception as exc:
                logger.debug(
                    "%s detection failed: %s",
                    provider_info["name"],
                    exc,
                )

        return self.detected_providers

    def get_available_models(
        self,
        provider_id: str,
    ) -> List[str]:
        if provider_id not in self.detected_providers:
            return []

        provider_info = self.detected_providers[
            provider_id
        ]
        host = provider_info["host"]
        endpoint = provider_info["models_endpoint"]

        try:
            response = requests.get(
                f"{host}{endpoint}",
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            if provider_id == "ollama":
                models = [
                    model["name"]
                    for model in data.get(
                        "models",
                        [],
                    )
                    if model.get("name")
                ]
            else:
                models = [
                    model["id"]
                    for model in data.get(
                        "data",
                        [],
                    )
                    if model.get("id")
                ]

            self.available_models[provider_id] = (
                models
            )
            return models
        except Exception as exc:
            logger.error(
                "Failed to list models for %s: %s",
                provider_id,
                exc,
            )
            return []

    def test_model_connection(
        self,
        provider_id: str,
        model_name: str,
    ) -> bool:
        if provider_id not in self.detected_providers:
            return False

        provider_info = self.detected_providers[
            provider_id
        ]
        try:
            provider = create_provider(
                provider_id=provider_id,
                model=model_name,
                host=provider_info["host"],
            )
            provider.generate(
                "Reply with OK.",
                max_tokens=8,
                temperature=0.0,
            )
            return True
        except Exception as exc:
            logger.error(
                "Model test failed for %s/%s: %s",
                provider_id,
                model_name,
                exc,
            )
            return False

    def get_provider_status(self) -> Dict[str, Dict]:
        status = {}

        for provider_id, provider_info in (
            self.providers.items()
        ):
            is_available = (
                provider_id
                in self.detected_providers
            )
            models = self.available_models.get(
                provider_id,
                [],
            )

            status[provider_id] = {
                "name": provider_info["name"],
                "icon": provider_info["icon"],
                "available": is_available,
                "host": provider_info[
                    "default_host"
                ],
                "model_count": len(models),
                "models": models,
            }

        return status

    def get_recommended_provider(
        self,
    ) -> Optional[str]:
        if not self.detected_providers:
            return None

        return max(
            self.detected_providers,
            key=lambda provider_id: len(
                self.available_models.get(
                    provider_id,
                    [],
                )
            ),
        )

    def create_config_for_provider(
        self,
        provider_id: str,
        model_name: Optional[str] = None,
    ) -> Dict:
        if provider_id not in self.detected_providers:
            raise ValueError(
                f"Provider {provider_id} is not available"
            )

        provider_info = self.detected_providers[
            provider_id
        ]

        if not model_name:
            models = self.available_models.get(
                provider_id,
                [],
            )
            if not models:
                raise ValueError(
                    "No models available for "
                    f"{provider_id}"
                )
            model_name = models[0]

        return {
            "llm_provider": provider_id,
            "llm_host": provider_info["host"],
            "model": model_name,
        }

    def save_config(
        self,
        config: Dict,
        config_path: str = "config.yaml",
    ) -> bool:
        try:
            with open(
                config_path,
                "w",
                encoding="utf-8",
            ) as handle:
                yaml.safe_dump(
                    config,
                    handle,
                    default_flow_style=False,
                    sort_keys=True,
                )
            return True
        except Exception as exc:
            logger.error(
                "Failed to save configuration: %s",
                exc,
            )
            return False

    def load_config(
        self,
        config_path: str = "config.yaml",
    ) -> Dict:
        try:
            with open(
                config_path,
                "r",
                encoding="utf-8",
            ) as handle:
                config = yaml.safe_load(handle)
            return config or {}
        except Exception as exc:
            logger.error(
                "Failed to load configuration: %s",
                exc,
            )
            return {}

    def get_installation_instructions(
        self,
        provider_id: str,
    ) -> str:
        instructions = {
            "ollama": (
                "1. Install Ollama\n"
                "2. Start the Ollama service\n"
                "3. Pull a compatible model\n"
                "4. Use the default host "
                "http://localhost:11434"
            ),
            "lm_studio": (
                "1. Install and launch LM Studio\n"
                "2. Download a local model\n"
                "3. Start the local API server\n"
                "4. Use the default host "
                "http://localhost:1234"
            ),
            "lm_studio_ci": (
                "1. Install the LM Studio command-line tooling\n"
                "2. Download a local model\n"
                "3. Start its API server\n"
                "4. Use the default host "
                "http://localhost:1234"
            ),
            "llama_cpp": (
                "1. Build or install llama.cpp with server support\n"
                "2. Start the server with a compatible model\n"
                "3. Use the default host "
                "http://localhost:8080"
            ),
        }
        return instructions.get(
            provider_id,
            "Installation instructions not available.",
        )

    def get_provider_info(
        self,
        provider_id: str,
    ) -> Dict:
        if provider_id not in self.providers:
            return {}

        info = self.providers[provider_id].copy()
        info["available"] = (
            provider_id
            in self.detected_providers
        )
        info["models"] = (
            self.available_models.get(
                provider_id,
                [],
            )
        )
        info["installation_instructions"] = (
            self.get_installation_instructions(
                provider_id
            )
        )
        return info
