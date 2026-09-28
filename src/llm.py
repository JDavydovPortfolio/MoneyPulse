#!/usr/bin/env python3
"""Structured field extraction backed by a configurable local LLM provider."""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from .llm_providers import LLMProvider, create_provider
from .schema import SCHEMA_VERSION

logger = logging.getLogger(__name__)


class LLMParser:
    """Extract MoneyPulse fields through a local model provider."""

    FIELD_NAMES = [
        "merchant_name",
        "ein_or_ssn",
        "document_type",
        "requested_amount",
        "address_street",
        "address_city",
        "address_state",
        "address_zip",
        "contact_phone",
        "contact_email",
        "business_type",
        "annual_revenue",
        "years_in_business",
        "processing_volume",
    ]

    MISSING_MARKERS = {
        "",
        "n/a",
        "na",
        "none",
        "null",
        "not found",
        "not provided",
        "unknown",
    }

    def __init__(
        self,
        model_name: str = "microsoft/phi-2",
        ollama_host: Optional[str] = None,
        model: Optional[str] = None,
        provider: str = "transformers",
        host: Optional[str] = None,
        provider_instance: Optional[LLMProvider] = None,
    ):
        requested_model = model or model_name
        resolved_host = host or ollama_host

        self.provider_id = provider or "transformers"
        self.provider = provider_instance or create_provider(
            provider_id=self.provider_id,
            model=requested_model,
            host=resolved_host,
        )
        self.model = self.provider.model
        self.host = resolved_host

    def parse_document(self, text: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """Parse document text into the versioned MoneyPulse extraction schema."""
        chunks = self._chunk_text(text)
        if not chunks:
            raise ValueError("Cannot parse an empty document")

        field_attempts: Dict[str, List[Dict[str, Any]]] = {}
        values: Dict[str, str] = {}
        for field in self.FIELD_NAMES:
            value, attempts = self._generate_field(field, chunks)
            values[field] = value
            field_attempts[field] = attempts

        source_file = filename or "unknown"
        structured_data = {
            "schema_version": SCHEMA_VERSION,
            "merchant_name": values["merchant_name"],
            "ein_or_ssn": values["ein_or_ssn"],
            "document_type": values["document_type"],
            "address": {
                "street": values["address_street"],
                "city": values["address_city"],
                "state": values["address_state"],
                "zip": values["address_zip"],
            },
            "contact_info": {
                "phone": values["contact_phone"],
                "email": values["contact_email"],
            },
            "business_info": {
                "business_type": values["business_type"],
                "annual_revenue": values["annual_revenue"],
                "years_in_business": values["years_in_business"],
                "processing_volume": values["processing_volume"],
            },
            "requested_amount": values["requested_amount"],
            "source_file": source_file,
            "flagged_issues": [],
            "llm_provider": self.provider_id,
            "llm_model": self.model,
            "review_state": "unreviewed",
            "review_approved": False,
            "provenance": {
                "source": "ocr",
                "source_file": source_file,
                "provider": self.provider_id,
                "model": self.model,
                "document_chunks": len(chunks),
                "field_attempts": field_attempts,
            },
        }

        logger.info(
            "Parsed document with provider=%s model=%s chunks=%s",
            self.provider_id,
            self.model,
            len(chunks),
        )
        return structured_data

    def _generate_field(
        self,
        field: str,
        chunks: List[str],
    ) -> Tuple[str, List[Dict[str, Any]]]:
        attempts: List[Dict[str, Any]] = []
        for chunk_index, chunk in enumerate(chunks):
            prompt = self._get_field_prompt(field, chunk)
            response = self.provider.generate(
                prompt,
                max_tokens=96,
                temperature=0.0,
            )
            raw_response = "" if response is None else str(response)
            attempts.append(
                {
                    "chunk_index": chunk_index,
                    "raw_response": raw_response,
                }
            )
            cleaned = self._clean_response(raw_response, field)
            if not self._is_missing_value(cleaned):
                return cleaned, attempts
        return "", attempts

    def _chunk_text(self, text: str, max_length: int = 512) -> List[str]:
        """Split text into word-bounded chunks, including very long paragraphs."""
        words = text.split()
        if not words:
            return []
        return [
            " ".join(words[index:index + max_length])
            for index in range(0, len(words), max_length)
        ]

    def _get_field_prompt(self, field: str, text: str) -> str:
        instructions = (
            "Return only the extracted value. If the value is not present in this "
            "text, return an empty string. Do not guess or explain. "
        )
        prompts = {
            "merchant_name": "Extract the merchant or business name from this text: ",
            "ein_or_ssn": "Find the tax ID, EIN number, or SSN from this text: ",
            "document_type": "Identify the document type (application, statement, invoice, etc.) from this text: ",
            "requested_amount": "Extract the requested loan or funding amount from this text: ",
            "address_street": "Extract only the street address (no city/state/zip) from this text: ",
            "address_city": "Extract only the city name from this text: ",
            "address_state": "Extract only the state (2-letter abbreviation preferred) from this text: ",
            "address_zip": "Extract only the ZIP code from this text: ",
            "contact_phone": "Find the phone number from this text: ",
            "contact_email": "Find the email address from this text: ",
            "business_type": "Extract the business type from this text: ",
            "annual_revenue": "Extract the annual revenue amount from this text: ",
            "years_in_business": "Extract the years in business from this text: ",
            "processing_volume": "Extract the credit card processing volume from this text: ",
        }
        return instructions + prompts.get(field, f"Extract the {field.replace('_', ' ')} from this text: ") + text

    def _clean_response(self, text: str, field: Optional[str] = None) -> str:
        cleaned = re.sub(r"\s+", " ", (text or "").strip())
        cleaned = cleaned.strip("` ")
        if not cleaned:
            return ""

        labels = {"answer", "value", "result"}
        if field:
            labels.update({field.lower(), field.replace("_", " ").lower()})
        if ":" in cleaned:
            prefix, remainder = cleaned.split(":", 1)
            if prefix.strip().lower() in labels:
                cleaned = remainder.strip()

        return cleaned.strip(" \"'")

    def _is_missing_value(self, value: str) -> bool:
        return value.strip().lower().rstrip(".") in self.MISSING_MARKERS

    def test_connection(self) -> bool:
        """Return provider availability without changing parser state."""
        return self.provider.test_connection()
