#!/usr/bin/env python3
"""Structured field extraction backed by a configurable local LLM provider."""

import logging
import re
from typing import Any, Dict, List, Optional

from .llm_providers import LLMProvider, create_provider

logger = logging.getLogger(__name__)


class LLMParser:
    """Extract MoneyPulse fields through a local model provider."""

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

    def parse_document(
        self,
        text: str,
        filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Parse document text and return the MoneyPulse field schema."""
        chunks = self._chunk_text(text)
        if not chunks:
            raise ValueError("Cannot parse an empty document")

        primary_text = chunks[0]
        structured_data = {
            "merchant_name": "",
            "ein_or_ssn": "",
            "document_type": "application",
            "address": {
                "street": "",
                "city": "",
                "state": "",
                "zip": "",
            },
            "contact_info": {
                "phone": "",
                "email": "",
            },
            "business_info": {
                "business_type": "",
                "annual_revenue": "",
                "years_in_business": "",
                "processing_volume": "",
            },
            "requested_amount": "",
            "source_file": filename or "unknown",
            "confidence_score": 0.7,
            "flagged_issues": [],
            "llm_provider": self.provider_id,
            "llm_model": self.model,
        }

        for field in [
            "merchant_name",
            "ein_or_ssn",
            "document_type",
            "requested_amount",
        ]:
            structured_data[field] = (
                self._generate_field(
                    field,
                    primary_text,
                )
            )

        for field in [
            "street",
            "city",
            "state",
            "zip",
        ]:
            structured_data["address"][field] = (
                self._generate_field(
                    f"address_{field}",
                    primary_text,
                )
            )

        for field in ["phone", "email"]:
            structured_data["contact_info"][field] = (
                self._generate_field(
                    f"contact_{field}",
                    primary_text,
                )
            )

        for field in [
            "business_type",
            "annual_revenue",
            "years_in_business",
            "processing_volume",
        ]:
            structured_data["business_info"][field] = (
                self._generate_field(
                    field,
                    primary_text,
                )
            )

        logger.info(
            "Parsed document with provider=%s model=%s",
            self.provider_id,
            self.model,
        )
        return structured_data

    def _generate_field(
        self,
        field: str,
        text: str,
    ) -> str:
        prompt = self._get_field_prompt(field, text)
        response = self.provider.generate(
            prompt,
            max_tokens=96,
            temperature=0.0,
        )
        return self._clean_response(response)

    def _chunk_text(
        self,
        text: str,
        max_length: int = 512,
    ) -> List[str]:
        """Split text into word-bounded chunks."""
        paragraphs = text.split("\n\n")
        chunks: List[str] = []
        current_chunk: List[str] = []
        current_length = 0

        for paragraph in paragraphs:
            paragraph_length = len(
                paragraph.split()
            )
            if (
                current_length + paragraph_length
                > max_length
                and current_chunk
            ):
                chunks.append(
                    " ".join(current_chunk)
                )
                current_chunk = [paragraph]
                current_length = paragraph_length
            else:
                current_chunk.append(paragraph)
                current_length += paragraph_length

        if current_chunk:
            joined = " ".join(
                current_chunk
            ).strip()
            if joined:
                chunks.append(joined)

        return chunks

    def _get_field_prompt(
        self,
        field: str,
        text: str,
    ) -> str:
        prompts = {
            "merchant_name": (
                "Extract the merchant or business "
                f"name from this text: {text}"
            ),
            "ein_or_ssn": (
                "Find the tax ID, EIN number, or "
                f"SSN from this text: {text}"
            ),
            "document_type": (
                "What type of document is this "
                "(application, statement, invoice, "
                f"etc.): {text}"
            ),
            "requested_amount": (
                "Extract the requested loan or "
                f"funding amount from this text: {text}"
            ),
            "address_street": (
                "Extract only the street address "
                "(no city/state/zip) from this text: "
                f"{text}"
            ),
            "address_city": (
                "Extract only the city name from "
                f"this address information: {text}"
            ),
            "address_state": (
                "Extract only the state "
                "(2-letter abbreviation preferred) "
                f"from this address: {text}"
            ),
            "address_zip": (
                "Extract only the ZIP code from "
                f"this address: {text}"
            ),
            "contact_phone": (
                f"Find the phone number from this text: {text}"
            ),
            "contact_email": (
                f"Find the email address from this text: {text}"
            ),
            "business_type": (
                "What type of business is described "
                f"in this text: {text}"
            ),
            "annual_revenue": (
                "Extract the annual revenue amount "
                f"from this text: {text}"
            ),
            "years_in_business": (
                "How many years has this business "
                "been operating according to the "
                f"text: {text}"
            ),
            "processing_volume": (
                "Find the credit card processing "
                f"volume from this text: {text}"
            ),
        }
        return prompts.get(
            field,
            (
                "Extract the "
                f"{field.replace('_', ' ')} "
                f"from this text: {text}"
            ),
        )

    def _clean_response(self, text: str) -> str:
        cleaned = re.sub(
            r"\s+",
            " ",
            text.strip(),
        )
        if ":" in cleaned:
            cleaned = cleaned.split(":")[-1].strip()
        return cleaned.strip(" \"'")

    def test_connection(self) -> bool:
        """Return provider availability without changing parser state."""
        return self.provider.test_connection()
