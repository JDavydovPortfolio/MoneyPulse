import json
import csv
import logging
from datetime import datetime
from typing import Dict, List, Optional
import os
import requests
from requests.auth import HTTPBasicAuth
import zeep  # For SOAP API
from urllib.parse import urljoin

class CRMSubmitter:
    """Handles CRM submission and logging."""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        self.log_file = os.path.join(output_dir, "crm.log")
        self.logger = logging.getLogger(__name__)
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
    
    def submit_document(self, parsed_data: Dict) -> Dict:
        """Submit document to CRM (mock implementation)."""
        try:
            # Generate clean JSON file
            json_filename = self._generate_json_file(parsed_data)
            
            # Mock CRM API call
            submission_result = self._mock_crm_submit(parsed_data)
            
            # Log submission
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
        
        # Clean data for CRM submission
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
        
        # Simulate API processing time
        time.sleep(random.uniform(0.5, 1.5))
        
        # Check validation status
        if parsed_data.get('validation_status') == 'failed':
            return {
                "status": "rejected",
                "reason": "Document failed validation checks",
                "crm_id": None,
                "timestamp": datetime.now().isoformat()
            }
        
        # Check confidence score
        confidence = parsed_data.get('confidence_score', 0.5)
        if confidence < 0.3:
            return {
                "status": "pending_review",
                "reason": "Low confidence score requires manual review",
                "crm_id": f"PENDING-{random.randint(10000, 99999)}",
                "timestamp": datetime.now().isoformat()
            }
        
        # Simulate 90% success rate for valid documents
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


class NetSuiteConnector:
    """NetSuite integration connector supporting SOAP, REST, and SuiteQL."""

    def __init__(self, config: Dict):
        """
        Initialize NetSuite connector.

        Args:
            config: Dictionary containing:
                - account_id: NetSuite account ID
                - consumer_key: OAuth consumer key (for REST)
                - consumer_secret: OAuth consumer secret (for REST)
                - token_id: OAuth token ID (for REST)
                - token_secret: OAuth token secret (for REST)
                - email: NetSuite user email (for SOAP)
                - password: NetSuite user password (for SOAP)
                - role_id: NetSuite role ID (for SOAP)
                - app_id: Application ID (for SOAP)
                - api_type: 'soap', 'rest', or 'suiteql'
        """
        self.config = config
        self.api_type = config.get('api_type', 'rest').lower()
        self.logger = logging.getLogger(__name__)

        # Base URLs
        self.rest_base_url = f"https://{config['account_id']}.suitetalk.api.netsuite.com/services/rest"
        self.soap_base_url = f"https://{config['account_id']}.suitetalk.api.netsuite.com/services/NetSuitePort_2023_1"

        # Initialize appropriate client
        if self.api_type == 'soap':
            self._init_soap_client()
        elif self.api_type == 'rest':
            self._init_rest_client()
        elif self.api_type == 'suiteql':
            self._init_suiteql_client()

    def _init_soap_client(self):
        """Initialize SOAP client."""
        try:
            from zeep import Client
            from zeep.transports import Transport
            from requests import Session

            # Create session with authentication
            session = Session()
            session.auth = HTTPBasicAuth(self.config['email'], self.config['password'])

            # Add required headers
            session.headers.update({
                'Content-Type': 'text/xml;charset=UTF-8',
                'SOAPAction': ''
            })

            transport = Transport(session=session)
            self.soap_client = Client(
                f"{self.soap_base_url}?wsdl",
                transport=transport
            )

            # Set application info
            self.soap_client.service.setApplicationInfo(
                applicationId=self.config.get('app_id', 'MoneyPulse')
            )

        except ImportError:
            raise ImportError("zeep package required for SOAP API. Install with: pip install zeep")

    def _init_rest_client(self):
        """Initialize REST client with OAuth."""
        self.session = requests.Session()

        # Set up OAuth 1.0 authentication
        from requests_oauthlib import OAuth1
        oauth = OAuth1(
            self.config['consumer_key'],
            self.config['consumer_secret'],
            self.config['token_id'],
            self.config['token_secret'],
            signature_method='HMAC-SHA256'
        )
        self.session.auth = oauth

        # Set headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def _init_suiteql_client(self):
        """Initialize SuiteQL client."""
        self._init_rest_client()  # SuiteQL uses REST transport

    def submit_financial_document(self, document_data: Dict) -> Dict:
        """
        Submit processed financial document to NetSuite.

        Args:
            document_data: Structured document data from MoneyPulse

        Returns:
            Dictionary with submission results
        """
        try:
            if self.api_type == 'soap':
                return self._submit_via_soap(document_data)
            elif self.api_type == 'rest':
                return self._submit_via_rest(document_data)
            elif self.api_type == 'suiteql':
                return self._submit_via_suiteql(document_data)
            else:
                raise ValueError(f"Unsupported API type: {self.api_type}")

        except Exception as e:
            self.logger.error(f"NetSuite submission failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "api_type": self.api_type,
                "timestamp": datetime.now().isoformat()
            }

    def _submit_via_soap(self, document_data: Dict) -> Dict:
        """Submit document via NetSuite SOAP API."""
        try:
            # Create customer record (example - adapt based on your needs)
            customer_data = self._map_to_customer_record(document_data)

            # Call NetSuite SOAP API
            response = self.soap_client.service.add(customer_data)

            return {
                "status": "success",
                "api_type": "soap",
                "netsuite_id": response.baseRef.internalId,
                "record_type": "customer",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "status": "failed",
                "api_type": "soap",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _submit_via_rest(self, document_data: Dict) -> Dict:
        """Submit document via NetSuite REST API."""
        try:
            # Create customer record
            customer_data = self._map_to_customer_record(document_data)

            # POST to NetSuite REST API
            url = urljoin(self.rest_base_url, "/record/v1/customer")
            response = self.session.post(url, json=customer_data)

            if response.status_code in [200, 201]:
                result = response.json()
                return {
                    "status": "success",
                    "api_type": "rest",
                    "netsuite_id": result.get('id'),
                    "record_type": "customer",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "failed",
                    "api_type": "rest",
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "timestamp": datetime.now().isoformat()
                }

        except Exception as e:
            return {
                "status": "failed",
                "api_type": "rest",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _submit_via_suiteql(self, document_data: Dict) -> Dict:
        """Submit document via SuiteQL."""
        try:
            # Example: Insert customer data using SuiteQL
            query = """
            INSERT INTO Customer (
                CompanyName, Email, Phone, Addr1, City, State, Zip
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?
            )
            """

            params = [
                document_data.get('merchant_information', {}).get('name', ''),
                document_data.get('contact_information', {}).get('email', ''),
                document_data.get('contact_information', {}).get('phone', ''),
                document_data.get('address', {}).get('street', ''),
                document_data.get('address', {}).get('city', ''),
                document_data.get('address', {}).get('state', ''),
                document_data.get('address', {}).get('zip', '')
            ]

            url = urljoin(self.rest_base_url, "/query/v1/suiteql")
            payload = {
                "q": query,
                "p": params
            }

            response = self.session.post(url, json=payload)

            if response.status_code in [200, 201]:
                result = response.json()
                return {
                    "status": "success",
                    "api_type": "suiteql",
                    "inserted_rows": result.get('rows_affected', 0),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "failed",
                    "api_type": "suiteql",
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "timestamp": datetime.now().isoformat()
                }

        except Exception as e:
            return {
                "status": "failed",
                "api_type": "suiteql",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _map_to_customer_record(self, document_data: Dict) -> Dict:
        """Map MoneyPulse document data to NetSuite customer record."""
        merchant_info = document_data.get('merchant_information', {})
        contact_info = document_data.get('contact_information', {})
        address_info = document_data.get('address', {})

        # SOAP format
        if self.api_type == 'soap':
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
                'customForm': '-40',  # Standard customer form
                'isPerson': False
            }

        # REST format
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
        """Query existing customer data using SuiteQL."""
        if self.api_type != 'suiteql':
            raise ValueError("SuiteQL required for customer queries")

        try:
            query = f"""
            SELECT
                CompanyName, Email, Phone,
                Addr1, City, State, Zip
            FROM
                Customer
            WHERE
                InternalId = ?
            """

            url = urljoin(self.rest_base_url, "/query/v1/suiteql")
            payload = {
                "q": query,
                "p": [customer_id]
            }

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


class NetSuiteSubmitter(CRMSubmitter):
    """Extended CRM submitter with NetSuite integration."""

    def __init__(self, output_dir: str = "output", netsuite_config: Optional[Dict] = None):
        super().__init__(output_dir)
        self.netsuite_config = netsuite_config
        self.netsuite_connector = None

        if netsuite_config:
            try:
                self.netsuite_connector = NetSuiteConnector(netsuite_config)
                self.logger.info("NetSuite connector initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize NetSuite connector: {str(e)}")

    def submit_document(self, parsed_data: Dict) -> Dict:
        """Submit document to both CRM and NetSuite if configured."""
        # First do the standard CRM submission
        crm_result = super().submit_document(parsed_data)

        # Then submit to NetSuite if configured
        netsuite_result = None
        if self.netsuite_connector:
            try:
                netsuite_result = self.netsuite_connector.submit_financial_document(
                    parsed_data
                )
                self.logger.info(f"NetSuite submission result: {netsuite_result}")
            except Exception as e:
                netsuite_result = {
                    "status": "failed",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                self.logger.error(f"NetSuite submission failed: {str(e)}")

        return {
            "crm_result": crm_result,
            "netsuite_result": netsuite_result,
            "integrated_submission": self.netsuite_connector is not None
        }