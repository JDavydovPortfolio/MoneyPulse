import requests
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

class LLMParser:
    """Handles document classification and field extraction using local LLM.

    Supports providers:
    - ollama (http://localhost:11434)
    - lmstudio (OpenAI-compatible, http://localhost:1234)
    - auto (try ollama first, then lmstudio)
    """
    
    def __init__(
        self,
        ollama_host: str = "http://localhost:11434",
        model: str = "phi",
        provider: str = "auto",
        lmstudio_host: str = "http://localhost:1234",
        api_key: str = None
    ):
        """Initialize LLM parser with provider configuration."""
        self.ollama_host = ollama_host
        self.lmstudio_host = lmstudio_host
        self.model = model
        self.provider = provider.lower() if provider else "auto"
        self.api_key = api_key or "sk-no-key-required"
        self.logger = logging.getLogger(__name__)
    
    def parse_document(self, text: str, filename: str) -> Dict:
        """Parse document text and extract structured data."""
        try:
            prompt = self._build_parsing_prompt(text)
            response = self._query_llm(prompt)
            
            # Try to extract JSON from response
            json_text = self._extract_json_from_response(response)
            parsed_data = json.loads(json_text)
            
            # Add metadata
            parsed_data['source_file'] = filename
            parsed_data['processing_timestamp'] = self._get_timestamp()
            parsed_data['extracted_text'] = text[:1000] + "..." if len(text) > 1000 else text
            
            return parsed_data
            
        except Exception as e:
            self.logger.error(f"LLM parsing failed for {filename}: {str(e)}")
            return self._create_error_response(filename, str(e), text)
    
    def _build_parsing_prompt(self, text: str) -> str:
        """Build optimized prompt for faster document parsing."""
        # Truncate text if too long to speed up processing
        max_text_length = 2000
        if len(text) > max_text_length:
            text = text[:max_text_length] + "..."
            
        return f"""Extract business information from this document as JSON. Look carefully for company names, business names, DBA names, and personal names.

{text}

Return ONLY valid JSON:
{{
    "document_type": "merchant_application|w9|voided_check|bank_statement|other",
    "merchant_name": "COMPANY NAME or BUSINESS NAME or DBA or PERSON NAME",
    "ein_or_ssn": "9-digit number only",
    "submission_date": "YYYY-MM-DD format",
    "requested_amount": "number only",
    "address": {{"street": "full street address", "city": "city name", "state": "2-letter state", "zip": "5-digit ZIP"}},
    "contact_info": {{"phone": "10-digit phone", "email": "email@domain.com"}},
    "business_info": {{"business_type": "type of business", "years_in_business": "number", "annual_revenue": "dollar amount"}},
    "flagged_issues": ["list any missing or invalid data"],
    "confidence_score": 0.8
}}

CRITICAL: Look for business/company names in headers, signatures, "DBA", "Doing Business As", contact sections, and anywhere a name appears. Extract the most prominent business or person name."""
    
    def _query_ollama(self, prompt: str) -> str:
        """Send prompt to Ollama and return response."""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "num_predict": 500,  # Reduced for faster response
                    "top_k": 40,
                    "repeat_penalty": 1.1
                }
            }
            
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json=payload,
                timeout=30  # Reduced from 120s
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
            
            return response.json()["response"]
            
        except requests.exceptions.ConnectionError:
            raise Exception("Cannot connect to Ollama. Please ensure 'ollama serve' is running.")
        except requests.exceptions.Timeout:
            raise Exception("Ollama request timed out (30s). Try with a smaller/faster model.")
        except Exception as e:
            raise Exception(f"Ollama query failed: {str(e)}")

    def _query_lmstudio(self, prompt: str) -> str:
        """Send prompt to LM Studio (OpenAI-compatible) and return response."""
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "Extract document data as JSON only."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "top_p": 0.9,
                "max_tokens": 500,  # Limit response length
                "stream": False
            }
            response = requests.post(
                f"{self.lmstudio_host}/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30  # Reduced from 120s
            )
            if response.status_code != 200:
                raise Exception(f"LM Studio API error: {response.status_code} - {response.text}")
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content")
            if not content:
                raise Exception("LM Studio returned empty response")
            return content
        except requests.exceptions.ConnectionError:
            raise Exception("Cannot connect to LM Studio. Please ensure the local server is running (Server > Start Local Server).")
        except requests.exceptions.Timeout:
            raise Exception("LM Studio request timed out (30s). Try with a smaller/faster model.")
        except Exception as e:
            raise Exception(f"LM Studio query failed: {str(e)}")

    def _query_llm(self, prompt: str) -> str:
        """Route query based on provider selection or availability."""
        if self.provider == "ollama":
            return self._query_ollama(prompt)
        if self.provider == "lmstudio":
            return self._query_lmstudio(prompt)

        # auto mode: smart detection - prefer LM Studio if both available (faster)
        lm_studio_available = False
        ollama_available = False
        
        # Quick check for LM Studio (prefer this)
        try:
            lm_response = requests.get(f"{self.lmstudio_host}/v1/models", timeout=2)
            if lm_response.status_code == 200:
                models = lm_response.json().get("data", [])
                lm_studio_available = len(models) > 0
        except Exception:
            pass
            
        # Quick check for Ollama
        try:
            ollama_response = requests.get(f"{self.ollama_host}/api/version", timeout=2)
            ollama_available = ollama_response.status_code == 200
        except Exception:
            pass
        
        # Use LM Studio if available (faster), otherwise Ollama
        if lm_studio_available:
            self.logger.info("Auto-detected: Using LM Studio")
            return self._query_lmstudio(prompt)
        elif ollama_available:
            self.logger.info("Auto-detected: Using Ollama")
            return self._query_ollama(prompt)
        else:
            raise Exception("No LLM providers available. Please start either LM Studio or Ollama.")
    
    def _extract_json_from_response(self, response: str) -> str:
        """Extract JSON object from LLM response."""
        # Find JSON object in response
        start = response.find('{')
        end = response.rfind('}') + 1
        
        if start == -1 or end == 0:
            raise Exception("No JSON object found in LLM response")
        
        json_text = response[start:end]
        
        # Validate it's proper JSON
        try:
            json.loads(json_text)
            return json_text
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON in LLM response: {str(e)}")
    
    def _create_error_response(self, filename: str, error: str, text: str = "") -> Dict:
        """Create error response structure."""
        return {
            "source_file": filename,
            "document_type": "error",
            "merchant_name": "",
            "ein_or_ssn": "",
            "submission_date": "",
            "requested_amount": "",
            "address": {
                "street": "",
                "city": "",
                "state": "",
                "zip": ""
            },
            "contact_info": {
                "phone": "",
                "email": ""
            },
            "business_info": {
                "business_type": "",
                "years_in_business": "",
                "annual_revenue": ""
            },
            "error": error,
            "flagged_issues": [f"Processing error: {error}"],
            "confidence_score": 0.0,
            "processing_timestamp": self._get_timestamp(),
            "extracted_text": text[:500] + "..." if len(text) > 500 else text
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.now().isoformat()
    
    def test_connection(self) -> Dict[str, str]:
        """Test connection to configured LLM provider(s) and return status info."""
        result = {"status": False, "provider": "none", "model": "none", "details": ""}
        
        if self.provider == "ollama":
            return self._test_ollama_connection()
        elif self.provider == "lmstudio":
            return self._test_lmstudio_connection()
        else:  # auto mode
            # Use same logic as _query_llm - prefer LM Studio
            lm_result = self._test_lmstudio_connection()
            if lm_result["status"]:
                lm_result["details"] = f"Auto-detected: {lm_result['details']}"
                return lm_result
            
            ollama_result = self._test_ollama_connection()
            if ollama_result["status"]:
                ollama_result["details"] = f"Auto-detected: {ollama_result['details']}"
                return ollama_result
            
            result["details"] = "No LLM providers available (tried LM Studio and Ollama)"
            return result

    def _test_ollama_connection(self) -> Dict[str, str]:
        """Test Ollama connection specifically."""
        try:
            r = requests.get(f"{self.ollama_host}/api/version", timeout=5)
            if r.status_code == 200:
                models_r = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
                if models_r.status_code == 200:
                    models = models_r.json().get("models", [])
                    if models:
                        actual_model = models[0].get("name", self.model)
                        return {
                            "status": True,
                            "provider": "ollama", 
                            "model": actual_model,
                            "details": f"Ollama server running with {len(models)} models"
                        }
        except Exception as e:
            pass
        return {"status": False, "provider": "none", "model": "none", "details": "Ollama not available"}

    def _test_lmstudio_connection(self) -> Dict[str, str]:
        """Test LM Studio connection specifically."""
        try:
            r = requests.get(f"{self.lmstudio_host}/v1/models", timeout=5)
            if r.status_code == 200:
                models_data = r.json()
                models = models_data.get("data", [])
                if models:
                    actual_model = models[0].get("id", self.model)
                    return {
                        "status": True,
                        "provider": "lmstudio",
                        "model": actual_model,
                        "details": f"LM Studio server running with {len(models)} models"
                    }
                else:
                    return {"status": False, "provider": "none", "model": "none", "details": "LM Studio running but no models loaded"}
        except Exception as e:
            pass
        return {"status": False, "provider": "none", "model": "none", "details": "LM Studio not available"}