"""Deterministic local output and optional, explicitly gated CRM integrations."""

import csv
import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional
from urllib.parse import urljoin

import requests
from requests.auth import HTTPBasicAuth


def spreadsheet_safe(value):
    """Keep untrusted CSV strings from being evaluated as spreadsheet formulas."""
    if isinstance(value, str) and (
        value.startswith(("\t", "\r", "\n"))
        or value.lstrip().startswith(("=", "+", "-", "@"))
    ):
        return "'" + value
    return value


def approval_problem(metadata) -> Optional[str]:
    """Enforce the same explicit approval gate at both public CRM entry points."""
    if not isinstance(metadata, dict) or metadata.get("validation_status") != "passed":
        return "External CRM submission requires successful deterministic validation"
    if metadata.get("review_approved") is not True:
        return "External CRM submission requires explicit human review approval"
    if metadata.get("review_state") != "approved":
        return "External CRM submission requires review_state='approved'"
    return None


class CRMSubmitter:
    """Prepare local artifacts for human review and optional downstream use."""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        self.log_file = os.path.join(output_dir, "crm.log")
        self.logger = logging.getLogger(__name__)
        os.makedirs(output_dir, exist_ok=True)

    def submit_document(self, parsed_data: Dict) -> Dict:
        """Prepare local JSON only; this method never transmits data externally."""
        try:
            json_filename = self._generate_json_file(parsed_data)
            validation_passed = parsed_data.get("validation_status") == "passed"
            local_result = {
                "status": "prepared" if validation_passed else "blocked",
                "destination": "local_only",
                "requires_human_review": parsed_data.get("requires_human_review", False),
                "review_approved": parsed_data.get("review_approved", False),
                "reason": (
                    None
                    if validation_passed
                    else "Document failed deterministic validation"
                ),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self._log_submission(parsed_data, local_result)
            return {
                "status": local_result["status"],
                "json_file": json_filename,
                "destination": "local_only",
                "result": local_result,
            }
        except Exception as exc:
            error_msg = str(exc)
            self.logger.error("Local output preparation failed: %s", error_msg)
            self._log_submission(
                parsed_data,
                {"status": "failed", "error": error_msg},
            )
            return {
                "status": "failed",
                "error": error_msg,
                "destination": "local_only",
            }

    def generate_csv_summary(self, processed_documents: List[Dict]) -> str:
        """Generate a review-oriented CSV summary without model confidence claims."""
        csv_filename = os.path.join(
            self.output_dir,
            f"submission_summary_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.csv",
        )
        fieldnames = [
            "source_file",
            "schema_version",
            "document_type",
            "merchant_name",
            "ein_or_ssn",
            "requested_amount",
            "phone",
            "email",
            "street",
            "city",
            "state",
            "zip",
            "validation_status",
            "review_state",
            "review_approved",
            "requires_human_review",
            "flagged_issues_count",
            "processing_timestamp",
        ]
        with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for doc in processed_documents:
                address = (
                    doc.get("address", {})
                    if isinstance(doc.get("address", {}), dict)
                    else {}
                )
                contact = (
                    doc.get("contact_info", {})
                    if isinstance(doc.get("contact_info", {}), dict)
                    else {}
                )
                row = {
                        "source_file": doc.get("source_file", ""),
                        "schema_version": doc.get("schema_version", ""),
                        "document_type": doc.get("document_type", ""),
                        "merchant_name": doc.get("merchant_name", ""),
                        "ein_or_ssn": doc.get("ein_or_ssn", ""),
                        "requested_amount": doc.get("requested_amount", ""),
                        "phone": contact.get("phone", ""),
                        "email": contact.get("email", ""),
                        "street": address.get("street", ""),
                        "city": address.get("city", ""),
                        "state": address.get("state", ""),
                        "zip": address.get("zip", ""),
                        "validation_status": doc.get("validation_status", ""),
                        "review_state": doc.get("review_state", ""),
                        "review_approved": doc.get("review_approved", False),
                        "requires_human_review": doc.get(
                            "requires_human_review", False
                        ),
                        "flagged_issues_count": len(doc.get("flagged_issues", [])),
                        "processing_timestamp": doc.get(
                            "processing_timestamp", ""
                        ),
                    }
                writer.writerow({key: spreadsheet_safe(value) for key, value in row.items()})
        self.logger.info("CSV summary generated: %s", csv_filename)
        return csv_filename

    def _build_crm_payload(self, parsed_data: Dict) -> Dict:
        """Map validated MoneyPulse data to the downstream integration shape."""
        return {
            "merchant_information": {
                "name": parsed_data.get("merchant_name", ""),
                "ein_or_ssn": parsed_data.get("ein_or_ssn", ""),
                "business_type": parsed_data.get("business_info", {}).get(
                    "business_type", ""
                ),
                "years_in_business": parsed_data.get("business_info", {}).get(
                    "years_in_business", ""
                ),
                "annual_revenue": parsed_data.get("business_info", {}).get(
                    "annual_revenue", ""
                ),
            },
            "contact_information": {
                "phone": parsed_data.get("contact_info", {}).get("phone", ""),
                "email": parsed_data.get("contact_info", {}).get("email", ""),
            },
            "address": {
                "street": parsed_data.get("address", {}).get("street", ""),
                "city": parsed_data.get("address", {}).get("city", ""),
                "state": parsed_data.get("address", {}).get("state", ""),
                "zip": parsed_data.get("address", {}).get("zip", ""),
            },
            "application_details": {
                "document_type": parsed_data.get("document_type", ""),
                "submission_date": parsed_data.get("submission_date", ""),
                "requested_amount": parsed_data.get("requested_amount", ""),
            },
            "processing_metadata": {
                "schema_version": parsed_data.get("schema_version", ""),
                "source_file": parsed_data.get("source_file", ""),
                "llm_provider": parsed_data.get("llm_provider", ""),
                "llm_model": parsed_data.get("llm_model", ""),
                "validation_status": parsed_data.get("validation_status", ""),
                "review_state": parsed_data.get("review_state", ""),
                "review_approved": parsed_data.get("review_approved", False),
                "requires_human_review": parsed_data.get(
                    "requires_human_review", False
                ),
                "flagged_issues": parsed_data.get("flagged_issues", []),
                "processing_timestamp": parsed_data.get(
                    "processing_timestamp", ""
                ),
                "validation_timestamp": parsed_data.get(
                    "validation_timestamp", ""
                ),
            },
        }

    def _generate_json_file(self, parsed_data: Dict) -> str:
        """Write a deterministic, reviewable local JSON artifact."""
        source_file = parsed_data.get("source_file", "unknown")
        safe_base = os.path.basename(os.path.splitext(source_file)[0]) or "unknown"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        json_filename = os.path.join(
            self.output_dir,
            f"{safe_base}_processed_{timestamp}.json",
        )
        with open(json_filename, "w", encoding="utf-8") as handle:
            json.dump(
                self._build_crm_payload(parsed_data),
                handle,
                indent=2,
                ensure_ascii=False,
            )
        return json_filename

    def _log_submission(self, parsed_data: Dict, result: Dict):
        """Log local output preparation without copying raw OCR/model text."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_file": parsed_data.get("source_file", ""),
            "validation_status": parsed_data.get("validation_status", ""),
            "review_state": parsed_data.get("review_state", ""),
            "submission_result": result,
        }
        try:
            with open(self.log_file, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(log_entry) + "\n")
        except Exception as exc:
            self.logger.error("Failed to write local output log: %s", exc)

    def get_submission_stats(self) -> Dict:
        """Summarize local output preparation results."""
        if not os.path.exists(self.log_file):
            return {"total": 0, "prepared": 0, "blocked": 0, "failed": 0}

        stats = {"total": 0, "prepared": 0, "blocked": 0, "failed": 0}
        try:
            with open(self.log_file, "r", encoding="utf-8") as handle:
                for line in handle:
                    try:
                        entry = json.loads(line.strip())
                    except json.JSONDecodeError:
                        continue
                    stats["total"] += 1
                    status = entry.get("submission_result", {}).get(
                        "status", "failed"
                    )
                    stats[status if status in stats else "failed"] += 1
        except Exception as exc:
            self.logger.error("Failed to read local output log: %s", exc)
        return stats


class EnterpriseCRMConnector:
    """Optional external CRM connector for SOAP, REST, or database gateways."""

    def __init__(self, config: Dict):
        self.config = config
        self.crm_type = config.get("crm_type", "rest").lower()
        self.logger = logging.getLogger(__name__)
        self.base_url = config.get("base_url", "").rstrip("/")
        self.auth_type = config.get("auth_type", "oauth")
        self.timeout_seconds = config.get("timeout_seconds", 30)

        if self.crm_type not in {"soap", "rest", "database"}:
            raise ValueError(f"Unsupported CRM type: {self.crm_type}")
        if not self.base_url:
            raise ValueError("base_url is required for enterprise CRM integration")

        if self.crm_type == "soap":
            self._init_soap_client()
        elif self.crm_type == "rest":
            self._init_rest_client()
        else:
            self._init_database_client()

    def _init_soap_client(self):
        """Initialize SOAP support only when that optional integration is used."""
        try:
            from requests import Session
            from zeep import Client
            from zeep.transports import Transport
        except ImportError as exc:
            raise ImportError(
                "SOAP CRM support requires optional dependencies. "
                "Install requirements-crm.txt."
            ) from exc

        session = Session()
        session.auth = HTTPBasicAuth(
            self.config["email"],
            self.config["password"],
        )
        session.headers.update(
            {
                "Content-Type": "text/xml;charset=UTF-8",
                "SOAPAction": "",
            }
        )
        transport = Transport(session=session, timeout=self.timeout_seconds)
        self.soap_client = Client(f"{self.base_url}?wsdl", transport=transport)

        set_application_info = getattr(
            self.soap_client.service,
            "setApplicationInfo",
            None,
        )
        if callable(set_application_info):
            set_application_info(
                applicationId=self.config.get("app_id", "MoneyPulse")
            )

    def _init_rest_client(self):
        """Initialize the HTTP session for REST-style CRM integrations."""
        self.session = requests.Session()

        if self.auth_type == "oauth":
            try:
                from requests_oauthlib import OAuth1
            except ImportError as exc:
                raise ImportError(
                    "OAuth CRM support requires optional dependencies. "
                    "Install requirements-crm.txt."
                ) from exc
            self.session.auth = OAuth1(
                self.config.get("consumer_key"),
                self.config.get("consumer_secret"),
                self.config.get("token_id"),
                self.config.get("token_secret"),
                signature_method="HMAC-SHA256",
            )
        elif self.auth_type == "basic":
            self.session.auth = HTTPBasicAuth(
                self.config.get("username"),
                self.config.get("password"),
            )
        elif self.auth_type == "api_key":
            self.session.headers.update(
                {"Authorization": f"Bearer {self.config.get('api_key')}"}
            )
        else:
            raise ValueError(f"Unsupported CRM auth_type: {self.auth_type}")

        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

    def _init_database_client(self):
        """Initialize the HTTP gateway used by the legacy database adapter."""
        self._init_rest_client()

    def submit_financial_document(self, document_data: Dict) -> Dict:
        """Transmit an already validated and explicitly approved CRM payload."""
        problem = approval_problem(document_data.get("processing_metadata"))
        if problem:
            return {"status": "blocked", "reason": problem}
        try:
            if self.crm_type == "soap":
                return self._submit_via_soap(document_data)
            if self.crm_type == "rest":
                return self._submit_via_rest(document_data)
            return self._submit_via_database(document_data)
        except Exception as exc:
            self.logger.error("CRM submission failed: %s", exc)
            return {
                "status": "failed",
                "error": str(exc),
                "crm_type": self.crm_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def _submit_via_soap(self, document_data: Dict) -> Dict:
        try:
            customer_data = self._map_to_customer_record(document_data)
            response = self.soap_client.service.add(customer_data)
            return {
                "status": "success",
                "crm_type": "soap",
                "record_id": getattr(
                    response,
                    "id",
                    getattr(response, "internalId", "unknown"),
                ),
                "record_type": "customer",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as exc:
            return {
                "status": "failed",
                "crm_type": "soap",
                "error": str(exc),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def _submit_via_rest(self, document_data: Dict) -> Dict:
        try:
            customer_data = self._map_to_customer_record(document_data)
            endpoint = self.config.get("customer_endpoint", "/customers")
            url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
            response = self.session.post(
                url,
                json=customer_data,
                timeout=self.timeout_seconds,
            )
            if response.status_code in {200, 201}:
                result = response.json()
                return {
                    "status": "success",
                    "crm_type": "rest",
                    "record_id": result.get(
                        "id",
                        result.get(
                            "customer_id",
                            result.get("internal_id"),
                        ),
                    ),
                    "record_type": "customer",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            return {
                "status": "failed",
                "crm_type": "rest",
                "error": f"HTTP {response.status_code}: {response.text}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as exc:
            return {
                "status": "failed",
                "crm_type": "rest",
                "error": str(exc),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def _submit_via_database(self, document_data: Dict) -> Dict:
        """Submit through the existing HTTP database gateway integration."""
        try:
            query = """
            INSERT INTO customers (
                company_name, email, phone, address_line1, city, state, zip_code,
                created_at, source_system
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """
            merchant = document_data.get("merchant_information", {})
            contact = document_data.get("contact_information", {})
            address = document_data.get("address", {})
            params = [
                merchant.get("name", ""),
                contact.get("email", ""),
                contact.get("phone", ""),
                address.get("street", ""),
                address.get("city", ""),
                address.get("state", ""),
                address.get("zip", ""),
                datetime.now(timezone.utc).isoformat(),
                "MoneyPulse",
            ]
            endpoint = self.config.get(
                "database_endpoint",
                "/api/database/execute",
            )
            url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
            response = self.session.post(
                url,
                json={"query": query, "parameters": params},
                timeout=self.timeout_seconds,
            )
            if response.status_code in {200, 201}:
                result = response.json()
                return {
                    "status": "success",
                    "crm_type": "database",
                    "affected_rows": result.get("rows_affected", 1),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            return {
                "status": "failed",
                "crm_type": "database",
                "error": f"HTTP {response.status_code}: {response.text}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as exc:
            return {
                "status": "failed",
                "crm_type": "database",
                "error": str(exc),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def _map_to_customer_record(self, document_data: Dict) -> Dict:
        """Map the validated downstream payload to the configured CRM shape."""
        merchant_info = document_data.get("merchant_information", {})
        contact_info = document_data.get("contact_information", {})
        address_info = document_data.get("address", {})

        if self.crm_type == "soap":
            return {
                "name": merchant_info.get("name", ""),
                "email": contact_info.get("email", ""),
                "phone": contact_info.get("phone", ""),
                "addressbookList": {
                    "addressbook": {
                        "addr1": address_info.get("street", ""),
                        "city": address_info.get("city", ""),
                        "state": address_info.get("state", ""),
                        "zip": address_info.get("zip", ""),
                        "country": "US",
                    }
                },
                "customForm": "-40",
                "isPerson": False,
            }

        return {
            "companyname": merchant_info.get("name", ""),
            "email": contact_info.get("email", ""),
            "phone": contact_info.get("phone", ""),
            "addressbook": {
                "items": [
                    {
                        "addr1": address_info.get("street", ""),
                        "city": address_info.get("city", ""),
                        "state": address_info.get("state", ""),
                        "zip": address_info.get("zip", ""),
                        "country": "US",
                    }
                ]
            },
        }

    def query_customer_data(self, customer_id: str) -> Dict:
        """Query existing customer data for REST/database integrations."""
        if self.crm_type not in {"rest", "database"}:
            raise ValueError(
                "REST or Database connection required for customer queries"
            )

        try:
            if self.crm_type == "database":
                query = """
                SELECT
                    company_name, email, phone,
                    address_line1, city, state, zip_code
                FROM
                    customers
                WHERE
                    id = ?
                """
                payload = {
                    "query": query,
                    "parameters": [customer_id],
                }
            else:
                payload = {
                    "customer_id": customer_id,
                    "fields": ["company_name", "email", "phone", "address"],
                }

            endpoint = self.config.get("query_endpoint", "/customers/search")
            url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
            response = self.session.post(
                url,
                json=payload,
                timeout=self.timeout_seconds,
            )
            if response.status_code == 200:
                return {
                    "status": "success",
                    "data": response.json(),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            return {
                "status": "failed",
                "error": f"HTTP {response.status_code}: {response.text}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as exc:
            return {
                "status": "failed",
                "error": str(exc),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }


class EnterpriseCRMSubmitter(CRMSubmitter):
    """Local output plus explicitly approved external CRM transmission."""

    def __init__(
        self,
        output_dir: str = "output",
        crm_config: Optional[Dict] = None,
    ):
        super().__init__(output_dir)
        self.crm_config = crm_config
        self.crm_connector = None
        self.crm_initialization_error: Optional[str] = None

        if crm_config:
            try:
                self.crm_connector = EnterpriseCRMConnector(crm_config)
                self.logger.info("Enterprise CRM connector initialized")
            except Exception as exc:
                self.crm_initialization_error = str(exc)
                self.logger.error(
                    "Failed to initialize CRM connector: %s",
                    self.crm_initialization_error,
                )

    def submit_document(self, parsed_data: Dict) -> Dict:
        """Prepare local output and transmit only after explicit human approval."""
        local_result = super().submit_document(parsed_data)
        problem = approval_problem(parsed_data)

        if local_result.get("status") == "failed":
            enterprise_result = {
                "status": "blocked",
                "reason": "External CRM submission requires successful local output preparation",
            }
        elif self.crm_config and not self.crm_connector:
            enterprise_result = {
                "status": "failed",
                "reason": "Enterprise CRM connector could not be initialized",
                "error": self.crm_initialization_error,
            }
        elif not self.crm_connector:
            enterprise_result = None
        elif problem:
            enterprise_result = {
                "status": "blocked",
                "reason": problem,
            }
        else:
            enterprise_result = self.crm_connector.submit_financial_document(
                self._build_crm_payload(parsed_data)
            )

        return {
            "local_output_result": local_result,
            "enterprise_crm_result": enterprise_result,
            "integrated_submission": self.crm_connector is not None,
        }
