"""Small, validated local configuration shared by desktop and headless usage."""

import os
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

import yaml

from .llm_detector import RECOMMENDED_MODEL
from .llm_providers import is_local_model_host
from .ocr import (
    DEFAULT_MAX_FILE_SIZE_MB,
    DEFAULT_MAX_IMAGE_PIXELS,
    DEFAULT_MAX_PDF_PAGES,
)

DEFAULT_CONFIG = {
    "llm_provider": "ollama",
    "model": RECOMMENDED_MODEL,
    "allow_remote_llm": False,
    "ocr_max_file_mb": DEFAULT_MAX_FILE_SIZE_MB,
    "ocr_max_pdf_pages": DEFAULT_MAX_PDF_PAGES,
    "ocr_max_image_pixels": DEFAULT_MAX_IMAGE_PIXELS,
}
CONFIG_FIELDS = {
    "llm_provider",
    "llm_host",
    "ollama_host",
    "model",
    "tesseract_path",
    "allow_remote_llm",
    "ocr_max_file_mb",
    "ocr_max_pdf_pages",
    "ocr_max_image_pixels",
}
TEXT_FIELDS = {"llm_provider", "llm_host", "ollama_host", "model", "tesseract_path"}
LIMIT_FIELDS = {"ocr_max_file_mb", "ocr_max_pdf_pages", "ocr_max_image_pixels"}
PROVIDERS = {"ollama", "lm_studio", "lm_studio_ci", "llama_cpp", "transformers"}


def validate_config(config):
    if not isinstance(config, dict) or set(config) - CONFIG_FIELDS:
        raise ValueError("Configuration must be a mapping containing only documented settings")
    for key in TEXT_FIELDS.intersection(config):
        value = config[key]
        if value is not None and not isinstance(value, str):
            raise ValueError(f"Configuration setting {key} must be text")
    if "allow_remote_llm" in config and type(config["allow_remote_llm"]) is not bool:
        raise ValueError("Configuration setting allow_remote_llm must be a boolean")
    for key in LIMIT_FIELDS.intersection(config):
        value = config[key]
        if type(value) is not int or value <= 0:
            raise ValueError(f"Configuration setting {key} must be a positive integer")
    if config.get("llm_provider", "ollama") not in PROVIDERS:
        raise ValueError("Unsupported LLM provider in configuration")
    if "model" in config and not (config["model"] or "").strip():
        raise ValueError("Model identifier must not be empty")
    for field in ("llm_host", "ollama_host"):
        if config.get(field):
            endpoint = urlsplit(config[field])
            if (
                endpoint.scheme not in {"http", "https"}
                or not endpoint.hostname
                or endpoint.username
                or endpoint.password
            ):
                raise ValueError(
                    "Model endpoint must be an HTTP(S) URL without embedded credentials"
                )
            if config.get("allow_remote_llm") is not True and not is_local_model_host(config[field]):
                raise ValueError(
                    "Remote model endpoints are disabled by default. "
                    "Set allow_remote_llm: true only when you intentionally want "
                    "OCR-derived document text sent to that endpoint."
                )
    return dict(config)


def load_config(path="config.yaml"):
    path = Path(path)
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as handle:
        try:
            return validate_config(yaml.safe_load(handle))
        except yaml.YAMLError as exc:
            raise ValueError("Configuration contains invalid YAML") from exc


def save_config(config, path="config.yaml"):
    """Replace configuration atomically; a failed write leaves existing settings intact."""
    config = validate_config(config)
    path = Path(path)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=".moneypulse-config-",
        delete=False,
    ) as handle:
        temporary = Path(handle.name)
        try:
            yaml.safe_dump(config, handle, sort_keys=True)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
