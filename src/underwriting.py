"""Deterministic underwriting pre-screen signals for MoneyPulse.

This module evaluates configurable business-policy thresholds against validated
merchant/application data. It is intentionally separate from the LLM so the
same extracted inputs produce the same rule result.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Dict, Optional


class UnderwritingPrecheck:
    """Calculate underwriting metrics and optional configurable rule outcomes."""

    def __init__(self, policy: Optional[Dict] = None):
        self.policy = dict(policy or {})

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
        """Return deterministic metrics and an optional policy pre-screen result.

        Supported policy keys:
        - min_years_in_business
        - min_annual_revenue
        - min_processing_volume
        - max_request_to_annual_revenue
        - max_request_to_processing_volume
        """
        business = document.get("business_info", {}) or {}
        requested_amount = self._decimal(document.get("requested_amount"))
        annual_revenue = self._decimal(business.get("annual_revenue"))
        processing_volume = self._decimal(business.get("processing_volume"))
        years_in_business = self._decimal(business.get("years_in_business"))

        metrics = {
            "requested_amount": float(requested_amount) if requested_amount is not None else None,
            "annual_revenue": float(annual_revenue) if annual_revenue is not None else None,
            "processing_volume": float(processing_volume) if processing_volume is not None else None,
            "years_in_business": float(years_in_business) if years_in_business is not None else None,
            "request_to_annual_revenue": self._ratio(requested_amount, annual_revenue),
            "request_to_processing_volume": self._ratio(requested_amount, processing_volume),
        }

        available_signals = sum(value is not None for value in (
            requested_amount,
            annual_revenue,
            processing_volume,
            years_in_business,
        ))

        result = {
            "mode": "policy" if self.policy else "signals_only",
            "status": "ready" if available_signals == 4 else "partial",
            "metrics": metrics,
            "rules": [],
            "preliminary_recommendation": "not_configured",
        }

        if not self.policy:
            return result

        rules = []

        def add_rule(name: str, actual, operator: str, threshold):
            if threshold is None:
                return
            threshold_decimal = self._decimal(threshold)
            if threshold_decimal is None:
                raise ValueError(f"Invalid underwriting policy threshold for {name}: {threshold!r}")
            if actual is None:
                rules.append({
                    "rule": name,
                    "result": "missing_data",
                    "actual": None,
                    "threshold": float(threshold_decimal),
                })
                return
            if operator == "min":
                passed = Decimal(str(actual)) >= threshold_decimal
            else:
                passed = Decimal(str(actual)) <= threshold_decimal
            rules.append({
                "rule": name,
                "result": "pass" if passed else "fail",
                "actual": float(actual),
                "threshold": float(threshold_decimal),
            })

        add_rule(
            "minimum_years_in_business",
            years_in_business,
            "min",
            self.policy.get("min_years_in_business"),
        )
        add_rule(
            "minimum_annual_revenue",
            annual_revenue,
            "min",
            self.policy.get("min_annual_revenue"),
        )
        add_rule(
            "minimum_processing_volume",
            processing_volume,
            "min",
            self.policy.get("min_processing_volume"),
        )
        add_rule(
            "maximum_request_to_annual_revenue",
            metrics["request_to_annual_revenue"],
            "max",
            self.policy.get("max_request_to_annual_revenue"),
        )
        add_rule(
            "maximum_request_to_processing_volume",
            metrics["request_to_processing_volume"],
            "max",
            self.policy.get("max_request_to_processing_volume"),
        )

        result["rules"] = rules
        if not rules:
            result["preliminary_recommendation"] = "not_configured"
        elif any(rule["result"] == "missing_data" for rule in rules):
            result["preliminary_recommendation"] = "needs_more_data"
        elif any(rule["result"] == "fail" for rule in rules):
            result["preliminary_recommendation"] = "manual_review"
        else:
            result["preliminary_recommendation"] = "advance"

        return result
