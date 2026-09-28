import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .crm_submit import CRMSubmitter
from .llm import LLMParser
from .ocr import OCRProcessor, SUPPORTED_EXTENSIONS
from .validator import DocumentValidator


class DocumentPipeline:
    """Main pipeline orchestrator for document processing."""

    def __init__(self, output_dir: str = "output", config: Optional[Dict] = None):
        self.output_dir = output_dir
        self.config = config or {}
        self.ocr = OCRProcessor(tesseract_path=self.config.get("tesseract_path"))
        self.llm = self._build_llm()
        self.validator = DocumentValidator()
        self.crm = CRMSubmitter(output_dir)
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            self._setup_logging()

    def _build_llm(self, config=None) -> LLMParser:
        config = self.config if config is None else config
        provider = config.get("llm_provider", "ollama")
        host = config.get("llm_host") or config.get("ollama_host")
        model = config.get("model", "gemma4:e2b-it-qat")
        return LLMParser(provider=provider, host=host, model=model)

    def process_directory(self, input_dir: str, progress_callback=None) -> List[Dict]:
        if not os.path.exists(input_dir):
            raise FileNotFoundError(f"Input directory not found: {input_dir}")
        files = [
            os.path.join(input_dir, filename)
            for filename in os.listdir(input_dir)
            if os.path.splitext(filename)[1].lower() in SUPPORTED_EXTENSIONS
        ]
        if not files:
            self.logger.warning("No supported documents found in %s", input_dir)
            return []
        processed_documents = []
        for index, file_path in enumerate(files):
            if progress_callback:
                progress_callback(index, len(files), f"Processing {os.path.basename(file_path)}")
            processed_documents.append(self.process_single_document(file_path))
        try:
            csv_file = self.crm.generate_csv_summary(processed_documents)
            self.logger.info("Generated CSV summary: %s", csv_file)
        except Exception as exc:
            self.logger.error("Failed to generate CSV summary: %s", exc)
        return processed_documents

    def process_single_document(self, file_path: str) -> Dict:
        filename = os.path.basename(file_path)
        start_time = datetime.now(timezone.utc)
        self.logger.info("Starting processing for %s", filename)
        try:
            if not os.path.isfile(file_path):
                raise FileNotFoundError(f"Input file not found: {file_path}")
            suffix = os.path.splitext(file_path)[1].lower()
            if suffix not in SUPPORTED_EXTENSIONS:
                raise ValueError(
                    f"Unsupported file type '{suffix or '<none>'}'. Supported types: PDF, PNG, JPG, JPEG"
                )

            extracted_text = self.ocr.extract_text(file_path)
            if not extracted_text.strip():
                raise ValueError("No text could be extracted from document")

            parsed_data = self.llm.parse_document(extracted_text, filename)
            validated_data = self.validator.validate_document(parsed_data)

            completed_at = datetime.now(timezone.utc)
            validated_data["processing_timestamp"] = completed_at.isoformat()
            output_result = self.crm.submit_document(validated_data)
            if output_result.get("status") == "failed":
                raise RuntimeError(output_result.get("error", "Local output preparation failed"))

            return {
                **validated_data,
                "extracted_text": extracted_text,
                "output_result": output_result,
                "processing_status": "completed",
                "processing_time_seconds": (completed_at - start_time).total_seconds(),
            }
        except Exception as exc:
            completed_at = datetime.now(timezone.utc)
            self.logger.error("Failed to process %s: %s", filename, exc)
            return {
                "source_file": filename,
                "error": str(exc),
                "processing_status": "failed",
                "processing_timestamp": completed_at.isoformat(),
                "processing_time_seconds": (completed_at - start_time).total_seconds(),
            }

    def test_system_components(self) -> Dict:
        results = {
            "ocr": {"status": "unknown", "details": ""},
            "llm": {"status": "unknown", "details": ""},
            "output_directory": {"status": "unknown", "details": ""},
        }
        try:
            results["ocr"] = (
                {"status": "ok", "details": "Tesseract OCR is working"}
                if self.ocr.test_installation()
                else {"status": "error", "details": "Tesseract OCR test failed"}
            )
        except Exception as exc:
            results["ocr"] = {"status": "error", "details": f"OCR error: {exc}"}

        try:
            if self.llm.test_connection():
                results["llm"] = {
                    "status": "ok",
                    "details": f"LLM provider and configured model are available ({self.llm.provider_id}: {self.llm.model})",
                }
            else:
                results["llm"] = {
                    "status": "error",
                    "details": f"Configured provider/model is unavailable ({self.llm.provider_id}: {self.llm.model})",
                }
        except Exception as exc:
            results["llm"] = {"status": "error", "details": f"LLM error: {exc}"}

        try:
            os.makedirs(self.output_dir, exist_ok=True)
            test_file = os.path.join(self.output_dir, "test_write.tmp")
            with open(test_file, "w", encoding="utf-8") as handle:
                handle.write("test")
            os.remove(test_file)
            results["output_directory"] = {
                "status": "ok",
                "details": f"Output directory writable: {self.output_dir}",
            }
        except Exception as exc:
            results["output_directory"] = {
                "status": "error",
                "details": f"Output directory error: {exc}",
            }
        return results

    def get_processing_statistics(self, processed_documents: List[Dict]) -> Dict:
        if not processed_documents:
            return {}
        total = len(processed_documents)
        successful = sum(1 for document in processed_documents if document.get("processing_status") == "completed")
        failed = total - successful
        validation_stats = self.validator.get_validation_summary(
            [document for document in processed_documents if document.get("processing_status") == "completed"]
        )
        submission_stats = self.crm.get_submission_stats()
        avg_processing_time = sum(
            document.get("processing_time_seconds", 0) for document in processed_documents
        ) / total
        return {
            "processing": {
                "total_documents": total,
                "successful": successful,
                "failed": failed,
                "success_rate": successful / total,
                "average_processing_time": avg_processing_time,
            },
            "validation": validation_stats,
            "output": submission_stats,
        }

    def _setup_logging(self):
        log_dir = os.path.join(self.output_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler = logging.FileHandler(
            os.path.join(log_dir, f"pipeline_{datetime.now().strftime('%Y%m%d')}.log")
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        self.logger.setLevel(logging.DEBUG)

    def update_config(self, new_config: Dict):
        candidate = {**self.config, **new_config}
        ocr = self.ocr
        llm = self.llm
        if {"llm_provider", "llm_host", "ollama_host", "model"}.intersection(new_config):
            llm = self._build_llm(candidate)
        if "tesseract_path" in new_config:
            ocr = OCRProcessor(tesseract_path=candidate["tesseract_path"])
        self.config = candidate
        self.ocr = ocr
        self.llm = llm
