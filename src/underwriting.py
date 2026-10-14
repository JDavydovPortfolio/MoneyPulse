"""Review-gated deterministic calculations for MoneyPulse.

This module never infers merchant financial facts and never makes an underwriting
approval decision. It only derives arithmetic metrics from values that already
exist in the structured document after explicit human approval.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Dict, Optional


class UnderwritingMetrics:
    """Calculate derived ratios only from explicitly reviewed document values."""

    @staticmethod
    def _decimal(value) -> Optional[Decimal]:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        cleaned = re.sub(r"[$,\s]", "", text)
        if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", cleaned):
            return None
        try:
            number = Decimal(cleaned)
        except InvalidOperation:
            return None
        return number if number.is_finite() and number >= 0 else None

    @staticmethod
    def _ratio(numerator: Optional[Decimal], denominator: Optional[Decimal]):
        if numerator is None or denominator in (None, Decimal("0")):
            return None
        return float((numerator / denominator).quantize(Decimal("0.0001")))

    def evaluate(self, document: Dict) -> Dict:
        """Return review-gated arithmetic derived from explicit source fields.

        Financial values such as annual revenue, processing volume, years in
        business, and requested amount must already be present in the reviewed
        structured document. Missing values are never estimated or invented.
        """
        if document.get("review_approved") is not True or document.get("review_state") != "approved":
            return {
                "status": "awaiting_review",
                "metrics": {},
            }

        business = document.get("business_info", {}) or {}
        requested_amount = self._decimal(document.get("requested_amount"))
        annual_revenue = self._decimal(business.get("annual_revenue"))
        processing_volume = self._decimal(business.get("processing_volume"))
        years_in_business = self._decimal(business.get("years_in_business"))

        inputs = {
            "requested_amount": float(requested_amount) if requested_amount is not None else None,
            "annual_revenue": float(annual_revenue) if annual_revenue is not None else None,
            "processing_volume": float(processing_volume) if processing_volume is not None else None,
            "years_in_business": float(years_in_business) if years_in_business is not None else None,
        }
        metrics = {
            "request_to_annual_revenue": self._ratio(requested_amount, annual_revenue),
            "request_to_processing_volume": self._ratio(requested_amount, processing_volume),
        }

        return {
            "status": "calculated",
            "inputs": inputs,
            "metrics": metrics,
        }
