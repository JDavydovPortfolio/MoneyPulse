#!/usr/bin/env python3
"""Local model integration used by the MoneyPulse processing pipeline."""

import logging
import re
from typing import Any, Dict, List

import torch
from transformers import pipeline

logger = logging.getLogger(__name__)


class LLMParser:
    """Extract structured fields with a locally loaded Transformers model.

    `ollama_host` is retained for backwards compatibility with existing
    configuration. Provider-specific HTTP inference is handled separately by
    the provider-detection modules and is not performed by this class yet.
    """

    MODEL_ALIASES = {
        "phi": "microsoft/phi-2",
    }

    def __init__(
        self,
        model_name: str = "microsoft/phi-2",
        ollama_host: str = "http://localhost:11434",
        model: str | None = None,
    ):
        requested_model = model or model_name
        resolved_model = self.MODEL_ALIASES.get(requested_model, requested_model)

        self.model = resolved_model
        self.ollama_host = ollama_host

        try:
            self.generator = pipeline(
                "text-generation",
                model=resolved_model,
                device="cuda" if torch.cuda.is_available() else "cpu",
            )
            logger.info("Initialized local Transformers model: %s", resolved_model)
        except Exception as exc:
            logger.error("Failed to initialize local model %s: %s", resolved_model, exc)
            raise

    def parse_document(self, text: str, filename: str | None = None) -> Dict[str, Any]:
        """Parse document text and return the current MoneyPulse field schema."""
        try:
            chunks = self._chunk_text(text)
            if not chunks:
                raise ValueError("Cannot parse an empty document")

            structured_data = {
                "merchant_name": "",
                "ein_or_ssn": "",
                "document_type": "application",
                "address": {"street": "", "city": "", "state": "", "zip": ""},
                "contact_info": {"phone": "", "email": ""},
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
            }

            direct_fields = [
                "merchant_name",
                "ein_or_ssn",
                "document_type",
                "requested_amount",
            ]
            for field in direct_fields:
                structured_data[field] = self._generate_field(field, chunks[0])

            for field in ["street", "city", "state", "zip"]:
                structured_data["address"][field] = self._generate_field(
                    f"address_{field}", chunks[0]
                )

            for field in ["phone", "email"]:
                structured_data["contact_info"][field] = self._generate_field(
                    f"contact_{field}", chunks[0]
                )

            for field in [
                "business_type",
                "annual_revenue",
                "years_in_business",
                "processing_volume",
            ]:
                structured_data["business_info"][field] = self._generate_field(
                    field, chunks[0]
                )

            logger.info("Successfully parsed document")
            return structured_data
        except Exception as exc:
            logger.error("Error parsing document: %s", exc)
            raise

    def _generate_field(self, field: str, text: str) -> str:
        prompt = self._get_field_prompt(field, text)
        response = self.generator(prompt, max_length=100, num_return_sequences=1)
        if not response:
            return ""

        first = response[0]
        if isinstance(first, dict) and "generated_text" in first:
            return self._clean_response(first["generated_text"])
        return self._clean_response(str(first))

    def _chunk_text(self, text: str, max_length: int = 512) -> List[str]:
        """Split text into word-bounded chunks."""
        paragraphs = text.split("\n\n")
        chunks: List[str] = []
        current_chunk: List[str] = []
        current_length = 0

        for paragraph in paragraphs:
            paragraph_length = len(paragraph.split())
            if current_length + paragraph_length > max_length and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [paragraph]
                current_length = paragraph_length
            else:
                current_chunk.append(paragraph)
                current_length += paragraph_length

        if current_chunk:
            joined = " ".join(current_chunk).strip()
            if joined:
                chunks.append(joined)

        return chunks

    def _get_field_prompt(self, field: str, text: str) -> str:
        prompts = {
            "merchant_name": f"Extract the merchant or business name from this text: {text}",
            "ein_or_ssn": f"Find the tax ID, EIN number, or SSN from this text: {text}",
            "document_type": f"What type of document is this (application, statement, invoice, etc.): {text}",
            "requested_amount": f"Extract the requested loan or funding amount from this text: {text}",
            "address_street": f"Extract only the street address (no city/state/zip) from this text: {text}",
            "address_city": f"Extract only the city name from this address information: {text}",
            "address_state": f"Extract only the state (2-letter abbreviation preferred) from this address: {text}",
            "address_zip": f"Extract only the ZIP code from this address: {text}",
            "contact_phone": f"Find the phone number from this text: {text}",
            "contact_email": f"Find the email address from this text: {text}",
            "business_type": f"What type of business is described in this text: {text}",
            "annual_revenue": f"Extract the annual revenue amount from this text: {text}",
            "years_in_business": f"How many years has this business been operating according to the text: {text}",
            "processing_volume": f"Find the credit card processing volume from this text: {text}",
        }
        return prompts.get(
            field, f"Extract the {field.replace('_', ' ')} from this text: {text}"
        )

    def _clean_response(self, text: str) -> str:
        if ":" in text:
            text = text.split(":")[-1]
        return re.sub(r"\s+", " ", text.strip())

    def test_connection(self) -> bool:
        """Run a small generation request against the loaded model."""
        try:
            self.generator(
                "Hello, this is a test.",
                max_length=20,
                num_return_sequences=1,
            )
            logger.info("Local model generation test successful")
            return True
        except Exception as exc:
            logger.error("Local model generation test failed: %s", exc)
            return False
