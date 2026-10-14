#!/usr/bin/env python3
"""Structured field extraction backed by a configurable local LLM provider."""

import logging
import re
from decimal import Decimal, InvalidOperation
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

    AMOUNT_FIELDS = {"requested_amount", "annual_revenue", "processing_volume"}
    DIGIT_FIELDS = {"ein_or_ssn", "contact_phone", "address_zip"}
    APPLICATION_INDICATORS = (
        "business name",
        "merchant name",
        "ein",
        "tax id",
        "requested funding",
        "requested amount",
        "address",
        "phone",
        "email",
    )

    def __init__(
        self,
        model_name: str = "qwen3:8b",
        ollama_host: Optional[str] = None,
        model: Optional[str] = None,
        provider: str = "ollama",
        host: Optional[str] = None,
        provider_instance: Optional[LLMProvider] = None,
        allow_remote_host: bool = False,
    ):
        requested_model = model or model_name
        resolved_host = host or ollama_host

        self.provider_id = provider or "transformers"
        self.provider = provider_instance or create_provider(
            provider_id=self.provider_id,
            model=requested_model,
            host=resolved_host,
            allow_remote_host=allow_remote_host,
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
        """Accept a model value only when it can be reconciled with its OCR chunk."""
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
            if self._is_missing_value(cleaned):
                continue
            if self._is_grounded(field, cleaned, chunk):
                return cleaned, attempts
            logger.warning(
                "Discarded ungrounded model value for field=%s chunk=%s",
                field,
                chunk_index,
            )
        return "", attempts

    @staticmethod
    def _normalize_text(value: str) -> str:
        return " ".join(re.findall(r"[a-z0-9]+", (value or "").casefold()))

    @staticmethod
    def _digits(value: str) -> str:
        return "".join(character for character in (value or "") if character.isdigit())

    @staticmethod
    def _parse_amount(value: str) -> Optional[Decimal]:
        text = re.sub(r"[$,\s]", "", value or "")
        if not re.fullmatch(r"[0-9]+(?:\.[0-9]{1,2})?", text):
            return None
        try:
            amount = Decimal(text)
        except InvalidOperation:
            return None
        return amount if amount.is_finite() else None

    def _amount_is_grounded(self, field: str, value: str, source: str) -> bool:
        target = self._parse_amount(value)
        if target is None:
            return False
        keywords = {
            "requested_amount": ("requested", "funding", "loan", "amount"),
            "annual_revenue": ("annual revenue", "revenue"),
            "processing_volume": ("processing", "volume"),
        }.get(field, ())
        pattern = re.compile(
            r"(?<![A-Za-z0-9])\$?\s*(?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.[0-9]{1,2})?"
        )
        normalized_source = source.casefold()
        for match in pattern.finditer(source):
            if self._parse_amount(match.group(0)) != target:
                continue
            start = max(0, match.start() - 80)
            end = min(len(source), match.end() + 80)
            context = normalized_source[start:end]
            if not keywords or any(keyword in context for keyword in keywords):
                return True
        return False

    def _digits_are_grounded(self, field: str, value: str, source: str) -> bool:
        target = self._digits(value)
        if not target:
            return False
        if field == "address_zip":
            return any(
                self._digits(candidate) == target
                for candidate in re.findall(r"(?<!\d)\d{5}(?:-\d{4})?(?!\d)", source)
            )
        if field == "contact_phone":
            candidates = re.findall(
                r"(?<!\d)(?:\+?1[ .()-]*)?(?:\(?\d{3}\)?[ .-]*)\d{3}[ .-]*\d{4}(?!\d)",
                source,
            )
            return any(self._digits(candidate)[-10:] == target[-10:] for candidate in candidates)
        if field == "ein_or_ssn":
            candidates = re.findall(
                r"(?<!\d)(?:\d{2}-\d{7}|\d{3}-\d{2}-\d{4}|\d{9})(?!\d)",
                source,
            )
            return any(self._digits(candidate) == target for candidate in candidates)
        return False

    def _is_grounded(self, field: str, value: str, source: str) -> bool:
        """Verify that a proposed field value is supported by the OCR source chunk."""
        if field in self.AMOUNT_FIELDS:
            return self._amount_is_grounded(field, value, source)

        if field in self.DIGIT_FIELDS:
            return self._digits_are_grounded(field, value, source)

        if field == "contact_email":
            return value.strip().casefold() in source.casefold()

        if field == "years_in_business":
            candidate = value.strip()
            match = re.search(
                rf"(?<![0-9]){re.escape(candidate)}(?![0-9])",
                source,
            )
            if not candidate or match is None:
                return False
            start = max(0, match.start() - 50)
            end = min(len(source), match.end() + 50)
            context = source[start:end].casefold()
            return "year" in context and "business" in context

        normalized_value = self._normalize_text(value)
        normalized_source = self._normalize_text(source)
        if not normalized_value:
            return False

        if field == "document_type":
            if normalized_value in normalized_source:
                return True
            if normalized_value == "application":
                matches = sum(
                    1
                    for indicator in self.APPLICATION_INDICATORS
                    if indicator in normalized_source
                )
                return matches >= 2
            return False

        return normalized_value in normalized_source

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
