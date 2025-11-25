import json
import csv
import logging
from datetime import datetime
from typing import Dict, List, Optional
import os
import requests
from requests.auth import HTTPBasicAuth
import zeep
from urllib.parse import urljoin

class CRMSubmitter:
    """Handles CRM submission and logging."""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        self.log_file = os.path.join(output_dir, "crm.log")
        self.logger = logging.getLogger(__name__)
        
        os.makedirs(output_dir, exist_ok=True)
    
    def submit_document(self, parsed_data: Dict) -> Dict:
        """Submit document to CRM (mock implementation)."""
        try:
            json_filename = self._generate_json_file(parsed_data)
            
            submission_result = self._mock_crm_submit(parsed_data)
            
            self._log_submission(parsed_data, submission_result)
            
            return {
                "status": "success",
                "json_file": json_filename,
                "crm_response": submission_result
            }
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"CRM submission failed: {error_msg}")
            self._log_submission(parsed_data, {"status": "failed", "error": error_msg})
            return {
                "status": "failed",
                "error": error_msg
            }
    
    def generate_csv_summary(self, processed_documents: List[Dict]) -> str:
        """Generate CSV summary of all processed documents."""
        csv_filename = os.path.join(self.output_dir, f"submission_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        
        try:
            with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'source_file', 'document_type', 'merchant_name', 'ein_or_ssn',
                    'requested_amount', 'phone', 'email', 'street', 'city', 'state', 'zip',
                    'validation_status', 'requires_human_review', 'confidence_score',
                    'flagged_issues_count', 'processing_timestamp'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for doc in processed_documents:
                    address = doc.get('address', {})
                    contact = doc.get('contact_info', {})
                    
                    row = {
                        'source_file': doc.get('source_file', ''),
                        'document_type': doc.get('document_type', ''),
                        'merchant_name': doc.get('merchant_name', ''),
                        'ein_or_ssn': doc.get('ein_or_ssn', ''),
                        'requested_amount': doc.get('requested_amount', ''),
                        'phone': contact.get('phone', ''),
                        'email': contact.get('email', ''),
                        'street': address.get('street', ''),
                        'city': address.get('city', ''),
                        'state': address.get('state', ''),
                        'zip': address.get('zip', ''),
                        'validation_status': doc.get('validation_status', ''),
                        'requires_human_review': doc.get('requires_human_review', False),
                        'confidence_score': doc.get('confidence_score', 0.0),
                        'flagged_issues_count': len(doc.get('flagged_issues', [])),
                        'processing_timestamp': doc.get('processing_timestamp', '')
                    }
                    writer.writerow(row)
            
            self.logger.info(f"CSV summary generated: {csv_filename}")
            return csv_filename
            
        except Exception as e:
            self.logger.error(f"Failed to generate CSV summary: {str(e)}")
            raise
    
    def _generate_json_file(self, parsed_data: Dict) -> str:
        """Generate clean JSON file for CRM upload."""
        source_file = parsed_data.get('source_file', 'unknown')
        base_name = os.path.splitext(source_file)[0]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_filename = os.path.join(self.output_dir, f"{base_name}_processed_{timestamp}.json")
        
        crm_data = {
            "merchant_information": {
                "name": parsed_data.get('merchant_name', ''),
                "ein_or_ssn": parsed_data.get('ein_or_ssn', ''),
                "business_type": parsed_data.get('business_info', {}).get('business_type', ''),
                "years_in_business": parsed_data.get('business_info', {}).get('years_in_business', ''),
                "annual_revenue": parsed_data.get('business_info', {}).get('annual_revenue', '')
            },
            "contact_information": {
                "phone": parsed_data.get('contact_info', {}).get('phone', ''),
                "email": parsed_data.get('contact_info', {}).get('email', '')
            },
            "address": {
                "street": parsed_data.get('address', {}).get('street', ''),
                "city": parsed_data.get('address', {}).get('city', ''),
                "state": parsed_data.get('address', {}).get('state', ''),
                "zip": parsed_data.get('address', {}).get('zip', '')
            },
            "application_details": {
                "document_type": parsed_data.get('document_type', ''),
                "submission_date": parsed_data.get('submission_date', ''),
                "requested_amount": parsed_data.get('requested_amount', '')
            },
            "processing_metadata": {
                "source_file": parsed_data.get('source_file', ''),
                "validation_status": parsed_data.get('validation_status', ''),
                "requires_human_review": parsed_data.get('requires_human_review', False),
                "confidence_score": parsed_data.get('confidence_score', 0.0),
                "flagged_issues": parsed_data.get('flagged_issues', []),
                "processing_timestamp": parsed_data.get('processing_timestamp', ''),
                "validation_timestamp": parsed_data.get('validation_timestamp', '')
            }
        }
        
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(crm_data, f, indent=2, ensure_ascii=False)
        
        return json_filename
    
    def _mock_crm_submit(self, parsed_data: Dict) -> Dict:
        """Mock CRM API submission."""
        import random
        import time
        
        time.sleep(random.uniform(0.5, 1.5))
        
        if parsed_data.get('validation_status') == 'failed':
            return {
                "status": "rejected",
                "reason": "Document failed validation checks",
                "crm_id": None,
                "timestamp": datetime.now().isoformat()
            }
        
        confidence = parsed_data.get('confidence_score', 0.5)
        if confidence < 0.3:
            return {
                "status": "pending_review",
                "reason": "Low confidence score requires manual review",
                "crm_id": f"PENDING-{random.randint(10000, 99999)}",
                "timestamp": datetime.now().isoformat()
            }
        
        if random.random() < 0.9:
            return {
                "status": "accepted",
                "crm_id": f"CRM-{random.randint(100000, 999999)}",
                "submission_time": datetime.now().isoformat(),
                "processing_notes": "Document successfully processed and entered into CRM"
            }
        else:
            return {
                "status": "failed",
                "reason": "CRM system temporarily unavailable",
                "crm_id": None,
                "timestamp": datetime.now().isoformat(),
                "retry_suggested": True
            }
    
    def _log_submission(self, parsed_data: Dict, result: Dict):
        """Log submission attempt to file."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "source_file": parsed_data.get('source_file', ''),
            "merchant_name": parsed_data.get('merchant_name', ''),
            "document_type": parsed_data.get('document_type', ''),
            "validation_status": parsed_data.get('validation_status', ''),
            "confidence_score": parsed_data.get('confidence_score', 0.0),
            "submission_result": result
        }
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            self.logger.error(f"Failed to write to CRM log: {str(e)}")
    
    def get_submission_stats(self) -> Dict:
        """Get submission statistics from log file."""
        if not os.path.exists(self.log_file):
            return {"total": 0, "accepted": 0, "rejected": 0, "failed": 0, "pending": 0}
        
        stats = {"total": 0, "accepted": 0, "rejected": 0, "failed": 0, "pending": 0}
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        stats["total"] += 1
                        status = entry.get("submission_result", {}).get("status", "unknown")
                        if status == "accepted":
                            stats["accepted"] += 1
                        elif status == "rejected":
                            stats["rejected"] += 1
                        elif status == "pending_review":
                            stats["pending"] += 1
                        else:
                            stats["failed"] += 1
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            self.logger.error(f"Failed to read CRM log: {str(e)}")
        
        return stats


class EnterpriseCRMConnector:
    """Enterprise CRM integration connector supporting SOAP, REST, and direct database access."""

    def __init__(self, config: Dict):
        """
        Initialize enterprise CRM connector.

        Args:
            config: Dictionary containing:
                - crm_type: 'soap', 'rest', or 'database'
                - base_url: Base URL for the CRM system
                - auth_type: Authentication method ('oauth', 'basic', 'api_key')
                - Various authentication parameters depending on auth_type
        """
        self.config = config
        self.crm_type = config.get('crm_type', 'rest').lower()
        self.logger = logging.getLogger(__name__)

        self.base_url = config.get('base_url', '').rstrip('/')
        self.auth_type = config.get('auth_type', 'oauth')

        if self.crm_type == 'soap':
            self._init_soap_client()
        elif self.crm_type == 'rest':
            self._init_rest_client()
        elif self.crm_type == 'database':
            self._init_database_client()

    def _init_soap_client(self):
        """Initialize SOAP client."""
        try:
            from zeep import Client
            from zeep.transports import Transport
            from requests import Session

            session = Session()
            session.auth = HTTPBasicAuth(self.config['email'], self.config['password'])

            session.headers.update({
                'Content-Type': 'text/xml;charset=UTF-8',
                'SOAPAction': ''
            })

            transport = Transport(session=session)
            self.soap_client = Client(
                f"{self.soap_base_url}?wsdl",
                transport=transport
            )

            self.soap_client.service.setApplicationInfo(
                applicationId=self.config.get('app_id', 'MoneyPulse')
            )

        except ImportError:
            raise ImportError("zeep package required for SOAP API. Install with: pip install zeep")

    def _init_rest_client(self):
        """Initialize REST client with flexible authentication."""
        self.session = requests.Session()

        if self.auth_type == 'oauth':
            from requests_oauthlib import OAuth1
            oauth = OAuth1(
                self.config.get('consumer_key'),
                self.config.get('consumer_secret'),
                self.config.get('token_id'),
                self.config.get('token_secret'),
                signature_method='HMAC-SHA256'
            )
            self.session.auth = oauth
        elif self.auth_type == 'basic':
            self.session.auth = HTTPBasicAuth(
                self.config.get('username'),
                self.config.get('password')
            )
        elif self.auth_type == 'api_key':
            self.session.headers.update({
                'Authorization': f"Bearer {self.config.get('api_key')}"
            })

        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def _init_database_client(self):
        """Initialize database client for direct database access."""
        self._init_rest_client()

    def submit_financial_document(self, document_data: Dict) -> Dict:
        """
        Submit processed financial document to enterprise CRM system.

        Args:
            document_data: Structured document data from MoneyPulse

        Returns:
            Dictionary with submission results
        """
        try:
            if self.crm_type == 'soap':
                return self._submit_via_soap(document_data)
            elif self.crm_type == 'rest':
                return self._submit_via_rest(document_data)
            elif self.crm_type == 'database':
                return self._submit_via_database(document_data)
            else:
                raise ValueError(f"Unsupported CRM type: {self.crm_type}")

        except Exception as e:
            self.logger.error(f"CRM submission failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "crm_type": self.crm_type,
                "timestamp": datetime.now().isoformat()
            }

    def _submit_via_soap(self, document_data: Dict) -> Dict:
        """Submit document via enterprise CRM SOAP API."""
        try:
            customer_data = self._map_to_customer_record(document_data)

            response = self.soap_client.service.add(customer_data)

            return {
                "status": "success",
                "crm_type": "soap",
                "record_id": getattr(response, 'id', getattr(response, 'internalId', 'unknown')),
                "record_type": "customer",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "status": "failed",
                "crm_type": "soap",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _submit_via_rest(self, document_data: Dict) -> Dict:
        """Submit document via enterprise CRM REST API."""
        try:
            customer_data = self._map_to_customer_record(document_data)

            endpoint = self.config.get('customer_endpoint', '/customers')
            url = urljoin(self.base_url + '/', endpoint.lstrip('/'))
            response = self.session.post(url, json=customer_data)

            if response.status_code in [200, 201]:
                result = response.json()
                return {
                    "status": "success",
                    "crm_type": "rest",
                    "record_id": result.get('id', result.get('customer_id', result.get('internal_id'))),
                    "record_type": "customer",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "failed",
                    "crm_type": "rest",
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "timestamp": datetime.now().isoformat()
                }

        except Exception as e:
            return {
                "status": "failed",
                "crm_type": "rest",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _submit_via_database(self, document_data: Dict) -> Dict:
        """Submit document via direct database access."""
        try:
            query = """
            INSERT INTO customers (
                company_name, email, phone, address_line1, city, state, zip_code,
                created_at, source_system
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """

            params = [
                document_data.get('merchant_information', {}).get('name', ''),
                document_data.get('contact_information', {}).get('email', ''),
                document_data.get('contact_information', {}).get('phone', ''),
                document_data.get('address', {}).get('street', ''),
                document_data.get('address', {}).get('city', ''),
                document_data.get('address', {}).get('state', ''),
                document_data.get('address', {}).get('zip', ''),
                datetime.now().isoformat(),
                'MoneyPulse'
            ]

            endpoint = self.config.get('database_endpoint', '/api/database/execute')
            url = urljoin(self.base_url + '/', endpoint.lstrip('/'))
            payload = {
                "query": query,
                "parameters": params
            }

            response = self.session.post(url, json=payload)

            if response.status_code in [200, 201]:
                result = response.json()
                return {
                    "status": "success",
                    "crm_type": "database",
                    "affected_rows": result.get('rows_affected', 1),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "failed",
                    "crm_type": "database",
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "timestamp": datetime.now().isoformat()
                }

        except Exception as e:
            return {
                "status": "failed",
                "crm_type": "database",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _map_to_customer_record(self, document_data: Dict) -> Dict:
        """Map MoneyPulse document data to enterprise CRM customer record."""
        merchant_info = document_data.get('merchant_information', {})
        contact_info = document_data.get('contact_information', {})
        address_info = document_data.get('address', {})

        if self.crm_type == 'soap':
            return {
                'name': merchant_info.get('name', ''),
                'email': contact_info.get('email', ''),
                'phone': contact_info.get('phone', ''),
                'addressbookList': {
                    'addressbook': {
                        'addr1': address_info.get('street', ''),
                        'city': address_info.get('city', ''),
                        'state': address_info.get('state', ''),
                        'zip': address_info.get('zip', ''),
                        'country': 'US'
                    }
                },
                'customForm': '-40',
                'isPerson': False
            }

        else:
            return {
                'companyname': merchant_info.get('name', ''),
                'email': contact_info.get('email', ''),
                'phone': contact_info.get('phone', ''),
                'addressbook': {
                    'items': [{
                        'addr1': address_info.get('street', ''),
                        'city': address_info.get('city', ''),
                        'state': address_info.get('state', ''),
                        'zip': address_info.get('zip', ''),
                        'country': 'US'
                    }]
                }
            }

    def query_customer_data(self, customer_id: str) -> Dict:
        """Query existing customer data using CRM query capabilities."""
        if self.crm_type not in ['rest', 'database']:
            raise ValueError("REST or Database connection required for customer queries")

        try:
            if self.crm_type == 'database':
                query = f"""
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
                    "parameters": [customer_id]
                }
            else:
                payload = {
                    "customer_id": customer_id,
                    "fields": ["company_name", "email", "phone", "address"]
                }

            endpoint = self.config.get('query_endpoint', '/customers/search')
            url = urljoin(self.base_url + '/', endpoint.lstrip('/'))

            response = self.session.post(url, json=payload)

            if response.status_code == 200:
                return {
                    "status": "success",
                    "data": response.json(),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "failed",
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "timestamp": datetime.now().isoformat()
                }

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


class EnterpriseCRMSubmitter(CRMSubmitter):
    """Extended CRM submitter with enterprise CRM integration."""

    def __init__(self, output_dir: str = "output", crm_config: Optional[Dict] = None):
        super().__init__(output_dir)
        self.crm_config = crm_config
        self.crm_connector = None

        if crm_config:
            try:
                self.crm_connector = EnterpriseCRMConnector(crm_config)
                self.logger.info("Enterprise CRM connector initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize CRM connector: {str(e)}")

    def submit_document(self, parsed_data: Dict) -> Dict:
        """Submit document to both local CRM and enterprise CRM if configured."""
        crm_result = super().submit_document(parsed_data)

        enterprise_crm_result = None
        if self.crm_connector:
            try:
                enterprise_crm_result = self.crm_connector.submit_financial_document(
                    parsed_data
                )
                self.logger.info(f"Enterprise CRM submission result: {enterprise_crm_result}")
            except Exception as e:
                enterprise_crm_result = {
                    "status": "failed",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                self.logger.error(f"Enterprise CRM submission failed: {str(e)}")

        return {
            "local_crm_result": crm_result,
            "enterprise_crm_result": enterprise_crm_result,
            "integrated_submission": self.crm_connector is not None
        }