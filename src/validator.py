import logging
import re
from decimal import Decimal
from datetime import datetime, timezone
from typing import Dict, List

from .schema import validate_extraction_schema


class DocumentValidator:
    """Apply deterministic structural and domain validation to parsed data."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def validate_document(self, parsed_data: Dict) -> Dict:
        """Validate parser output in place after enforcing the extraction schema."""
        validate_extraction_schema(parsed_data)
        validation_issues: List[str] = []

        ein_ssn = parsed_data.get("ein_or_ssn", "")
        if ein_ssn and not self._validate_ein_ssn(ein_ssn):
            validation_issues.append(
                f"Invalid EIN/SSN format: '{ein_ssn}' (must contain exactly 9 digits)"
            )

        zip_code = parsed_data.get("address", {}).get("zip", "")
        if zip_code and not self._validate_zip(zip_code):
            validation_issues.append(
                f"Invalid ZIP code: '{zip_code}' (must contain exactly 5 digits)"
            )

        amount = parsed_data.get("requested_amount", "")
        if amount and not self._validate_amount(amount):
            validation_issues.append(
                f"Invalid requested amount: '{amount}' (must be numeric)"
            )

        business = parsed_data["business_info"]
        for field in ("annual_revenue", "processing_volume"):
            if business[field] and not self._validate_amount(business[field]):
                validation_issues.append(f"Invalid {field}: '{business[field]}' (must be numeric)")
        years = business["years_in_business"]
        if years and re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", years.strip()) is None:
            validation_issues.append(f"Invalid years_in_business: '{years}' (must be non-negative numeric)")

        phone = parsed_data.get("contact_info", {}).get("phone", "")
        if phone and not self._validate_phone(phone):
            validation_issues.append(
                f"Invalid phone format: '{phone}' (must contain exactly 10 digits)"
            )

        email = parsed_data.get("contact_info", {}).get("email", "")
        if email and not self._validate_email(email):
            validation_issues.append(f"Invalid email format: '{email}'")

        state = parsed_data.get("address", {}).get("state", "")
        if state and not self._validate_state(state):
            validation_issues.append(
                f"Invalid state: '{state}' (must be a US 2-letter abbreviation)"
            )

        for field in ("merchant_name", "document_type"):
            if not parsed_data.get(field, "").strip():
                validation_issues.append(f"Missing required field: {field}")

        address = parsed_data.get("address", {})
        if any(address.values()) and not all(
            address.get(field) for field in ("street", "city", "state", "zip")
        ):
            validation_issues.append("Incomplete address information")

        existing_issues = parsed_data.get("flagged_issues", [])
        all_issues = list(dict.fromkeys([*existing_issues, *validation_issues]))
        parsed_data["flagged_issues"] = all_issues
        parsed_data["validation_status"] = "failed" if validation_issues else "passed"
        # Structural/domain checks cannot certify factual model accuracy.
        parsed_data["requires_human_review"] = True
        parsed_data["review_approved"] = False
        if validation_issues:
            parsed_data["review_state"] = "needs_correction"
        elif existing_issues:
            parsed_data["review_state"] = "needs_review"
        else:
            parsed_data["review_state"] = "ready_for_review"
        parsed_data["validation_timestamp"] = datetime.now(timezone.utc).isoformat()

        self.logger.info(
            "Validation completed for %s: %s domain issues",
            parsed_data.get("source_file", "unknown"),
            len(validation_issues),
        )
        return parsed_data

    def _validate_ein_ssn(self, ein_ssn: str) -> bool:
        return re.fullmatch(r"(?:[0-9]{9}|[0-9]{2}-[0-9]{7}|[0-9]{3}-[0-9]{2}-[0-9]{4})", (ein_ssn or "").strip()) is not None

    def _validate_zip(self, zip_code: str) -> bool:
        return re.fullmatch(r"[0-9]{5}", (zip_code or "").strip()) is not None

    def _validate_amount(self, amount: str) -> bool:
        try:
            text = str(amount).strip()
            if not text:
                return False
            if not re.fullmatch(r"\$?\s*(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)(?:\.[0-9]{1,2})?", text):
                return False
            clean_amount = re.sub(r"[$,\s]", "", text)
            return Decimal(clean_amount).is_finite()
        except (ValueError, TypeError):
            return False

    def _validate_phone(self, phone: str) -> bool:
        if re.fullmatch(r"[0-9()\s.\-]+", (phone or "").strip()) is None:
            return False
        clean_phone = re.sub(r"[^\d]", "", phone or "")
        return len(clean_phone) == 10 and clean_phone.isdigit()

    def _validate_email(self, email: str) -> bool:
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, (email or "").strip()) is not None

    def _validate_state(self, state: str) -> bool:
        valid_states = {
            "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
            "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
            "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
            "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
            "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC",
        }
        return (state or "").upper().strip() in valid_states

    def get_validation_summary(self, processed_documents: List[Dict]) -> Dict:
        total_docs = len(processed_documents)
        if total_docs == 0:
            return {}
        passed = sum(
            1 for doc in processed_documents if doc.get("validation_status") == "passed"
        )
        failed = total_docs - passed
        needs_review = sum(
            1 for doc in processed_documents if doc.get("requires_human_review", False)
        )
        ready_for_review = sum(
            1 for doc in processed_documents if doc.get("review_state") == "ready_for_review"
        )
        common_issues = {}
        for doc in processed_documents:
            for issue in doc.get("flagged_issues", []):
                common_issues[issue] = common_issues.get(issue, 0) + 1
        return {
            "total_documents": total_docs,
            "validation_passed": passed,
            "validation_failed": failed,
            "requires_human_review": needs_review,
            "ready_for_review": ready_for_review,
            "pass_rate": passed / total_docs,
            "common_issues": sorted(
                common_issues.items(), key=lambda item: item[1], reverse=True
            )[:5],
        }
