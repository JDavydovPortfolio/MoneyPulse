#!/usr/bin/env python3
"""
Optional LLM Integration Module
Only loads AI dependencies if they're available, falls back to basic parsing otherwise
"""

import logging
import re
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class LLMParser:
    """LLM parser with optional AI dependencies."""
    
    def __init__(self, model_name: str = "microsoft/phi-2", ollama_host: str = "http://localhost:11434", model: str = None):
        """Initialize LLM parser, falling back to basic parsing if AI libraries unavailable."""
        self.has_ai = False
        self.model_name = model_name
        self.ollama_host = ollama_host
        
        try:
            import torch
            from transformers import pipeline
            
            self.generator = pipeline(
                "text-generation",
                model=model_name,
                device="cuda" if torch.cuda.is_available() else "cpu"
            )
            self.has_ai = True
            logger.info(f"✅ AI enabled - Using model: {model_name}")
            
        except ImportError as e:
            logger.warning(f"⚠️ AI libraries not available, using basic parsing: {e}")
            self.has_ai = False
            
        except Exception as e:
            logger.warning(f"⚠️ AI initialization failed, using basic parsing: {e}")
            self.has_ai = False
    
    def parse_document(self, text: str, filename: str = None) -> Dict[str, Any]:
        """Parse document using AI if available, otherwise use basic regex parsing."""
        
        if self.has_ai:
            return self._parse_with_ai(text, filename)
        else:
            return self._parse_basic(text, filename)
    
    def _parse_with_ai(self, text: str, filename: str = None) -> Dict[str, Any]:
        """Parse using AI models."""
        try:
            prompt = self._create_parsing_prompt(text)
            
            response = self.generator(
                prompt,
                max_length=512,
                num_return_sequences=1,
                temperature=0.3,
                do_sample=True,
                truncation=True
            )
            
            generated_text = response[0]['generated_text']
            return self._structure_response(generated_text, filename)
            
        except Exception as e:
            logger.error(f"AI parsing failed, falling back to basic: {e}")
            return self._parse_basic(text, filename)
    
    def _parse_basic(self, text: str, filename: str = None) -> Dict[str, Any]:
        """Basic regex-based parsing when AI is not available."""
        
        logger.info("🔧 Using basic regex parsing (no AI)")
        
        result = {
            "filename": filename or "unknown",
            "parsing_method": "basic_regex",
            "business_name": "",
            "contact_info": {},
            "tax_id": "",
            "bank_info": {},
            "extracted_fields": {},
            "confidence": "low",
            "warnings": ["AI parsing not available - using basic regex patterns"]
        }
        
        patterns = {
            "business_name": r"(?:business|company|entity)\s+name[:\s]+([^\n\r]+)",
            "phone": r"(\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4})",
            "email": r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
            "ssn_ein": r"(?:SSN|EIN|Tax\s+ID)[:\s]*([0-9-]{9,11})",
            "routing": r"(?:routing|ABA)[:\s]*([0-9]{9})",
            "account": r"(?:account)[:\s]*([0-9]{4,17})",
        }
        
        for field, pattern in patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                result["extracted_fields"][field] = matches[0] if len(matches) == 1 else matches
        
        if "business_name" in result["extracted_fields"]:
            result["business_name"] = result["extracted_fields"]["business_name"]
        
        if any(field in result["extracted_fields"] for field in ["phone", "email"]):
            result["contact_info"] = {
                "phone": result["extracted_fields"].get("phone", ""),
                "email": result["extracted_fields"].get("email", "")
            }
        
        if "ssn_ein" in result["extracted_fields"]:
            result["tax_id"] = result["extracted_fields"]["ssn_ein"]
        
        if any(field in result["extracted_fields"] for field in ["routing", "account"]):
            result["bank_info"] = {
                "routing": result["extracted_fields"].get("routing", ""),
                "account": result["extracted_fields"].get("account", "")
            }
        
        return result
    
    def _create_parsing_prompt(self, text: str) -> str:
        """Create prompt for AI parsing."""
        return f"""Extract merchant information from this document:

{text[:1000]}

Extract the following information in JSON format:
- business_name
- contact_info (phone, email, address)
- tax_id (SSN/EIN)
- bank_info (routing, account)
- document_type

Response:"""
    
    def _structure_response(self, generated_text: str, filename: str) -> Dict[str, Any]:
        """Structure the AI response into our standard format."""
        try:
            import json
            
            json_start = generated_text.find('{')
            json_end = generated_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = generated_text[json_start:json_end]
                parsed = json.loads(json_str)
                
                result = {
                    "filename": filename or "unknown",
                    "parsing_method": "ai_enhanced",
                    "business_name": parsed.get("business_name", ""),
                    "contact_info": parsed.get("contact_info", {}),
                    "tax_id": parsed.get("tax_id", ""),
                    "bank_info": parsed.get("bank_info", {}),
                    "extracted_fields": parsed,
                    "confidence": "high",
                    "warnings": []
                }
                return result
                
        except Exception as e:
            logger.warning(f"Failed to parse AI response as JSON: {e}")
        
        return {
            "filename": filename or "unknown",
            "parsing_method": "ai_unstructured",
            "raw_response": generated_text,
            "confidence": "medium",
            "warnings": ["AI response could not be parsed as structured data"]
        }