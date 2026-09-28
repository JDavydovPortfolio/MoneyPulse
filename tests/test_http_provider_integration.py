import json
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from src.llm import LLMParser


FIELD_VALUES = {
    "merchant_name": "Example Harbor Coffee LLC",
    "ein_or_ssn": "99-9999999",
    "document_type": "application",
    "requested_amount": "$75000",
    "address_street": "123 Example Avenue",
    "address_city": "New York",
    "address_state": "NY",
    "address_zip": "10001",
    "contact_phone": "2125550100",
    "contact_email": "finance@example.com",
    "business_type": "Coffee Shop",
    "annual_revenue": "$525000",
    "years_in_business": "4",
    "processing_volume": "$48000",
}


def _value_for_prompt(prompt: str) -> str:
    lower = prompt.lower()
    checks = [
        ("street address", "address_street"),
        ("city name", "address_city"),
        ("state (2-letter", "address_state"),
        ("zip code", "address_zip"),
        ("phone number", "contact_phone"),
        ("email address", "contact_email"),
        ("merchant or business name", "merchant_name"),
        ("tax id", "ein_or_ssn"),
        ("identify the document type", "document_type"),
        ("requested loan or funding amount", "requested_amount"),
        ("business type", "business_type"),
        ("annual revenue amount", "annual_revenue"),
        ("years in business", "years_in_business"),
        ("processing volume", "processing_volume"),
    ]
    for needle, key in checks:
        if needle in lower:
            return FIELD_VALUES[key]
    return ""


class ProviderHandler(BaseHTTPRequestHandler):
    request_payloads = []

    def log_message(self, format, *args):
        return

    def _send_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/tags":
            self._send_json({"models": [{"name": "gemma4:e4b"}]})
            return
        if self.path == "/v1/models":
            self._send_json({"data": [{"id": "google/gemma-4-e4b"}]})
            return
        self._send_json({"error": "not found"}, status=404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length) or b"{}")
        type(self).request_payloads.append((self.path, payload))

        if self.path == "/api/generate":
            self._send_json({"response": _value_for_prompt(payload.get("prompt", ""))})
            return
        if self.path == "/v1/chat/completions":
            messages = payload.get("messages", [])
            prompt = messages[-1].get("content", "") if messages else ""
            self._send_json({"choices": [{"message": {"content": _value_for_prompt(prompt)}}]})
            return
        if self.path == "/api/v1/chat":
            prompt = payload.get("input", "")
            self._send_json({"output": [
                {"type": "reasoning", "content": "synthetic hidden reasoning"},
                {"type": "message", "content": _value_for_prompt(prompt)},
            ]})
            return
        self._send_json({"error": "not found"}, status=404)


@contextmanager
def _provider_server():
    ProviderHandler.request_payloads = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), ProviderHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


DOCUMENT_TEXT = """
Example Harbor Coffee LLC application
EIN 99-9999999
123 Example Avenue, New York, NY 10001
finance@example.com 212-555-0100
Requested funding amount $75,000
Coffee Shop annual revenue $525,000, 4 years in business, processing volume $48,000
"""


def test_real_ollama_http_path_extracts_structured_fields():
    with _provider_server() as host:
        parser = LLMParser(provider="ollama", host=host, model="gemma4:e4b")
        result = parser.parse_document(DOCUMENT_TEXT, "synthetic.txt")

    assert result["merchant_name"] == FIELD_VALUES["merchant_name"]
    assert result["requested_amount"] == FIELD_VALUES["requested_amount"]
    assert result["llm_provider"] == "ollama"
    assert result["llm_model"] == "gemma4:e4b"
    generate_payloads = [payload for path, payload in ProviderHandler.request_payloads if path == "/api/generate"]
    assert generate_payloads
    assert all(payload["think"] is False for payload in generate_payloads)
    assert all(payload["options"]["temperature"] == 0.0 for payload in generate_payloads)


def test_real_lm_studio_http_path_extracts_structured_fields():
    with _provider_server() as host:
        parser = LLMParser(provider="lm_studio", host=host, model="google/gemma-4-e4b")
        result = parser.parse_document(DOCUMENT_TEXT, "synthetic.txt")

    assert result["merchant_name"] == FIELD_VALUES["merchant_name"]
    assert result["requested_amount"] == FIELD_VALUES["requested_amount"]
    assert result["llm_provider"] == "lm_studio"
    assert result["llm_model"] == "google/gemma-4-e4b"
    chat_payloads = [payload for path, payload in ProviderHandler.request_payloads if path == "/api/v1/chat"]
    assert chat_payloads
    assert all(payload["temperature"] == 0.0 for payload in chat_payloads)
    assert all(payload["reasoning"] == "off" for payload in chat_payloads)
