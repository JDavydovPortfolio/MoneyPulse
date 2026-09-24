import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

from .crm_submit import CRMSubmitter
from .llm import LLMParser
from .ocr import OCRProcessor
from .validator import DocumentValidator


class DocumentPipeline:
    """Main pipeline orchestrator for document processing."""

    def __init__(
        self,
        output_dir: str = "output",
        config: Optional[Dict] = None,
    ):
        self.output_dir = output_dir
        self.config = config or {}

        self.ocr = OCRProcessor(
            tesseract_path=self.config.get(
                "tesseract_path"
            )
        )
        self.llm = self._build_llm()
        self.validator = DocumentValidator()
        self.crm = CRMSubmitter(output_dir)

        self.logger = logging.getLogger(__name__)

        if not self.logger.handlers:
            self._setup_logging()

    def _build_llm(self) -> LLMParser:
        provider = self.config.get(
            "llm_provider",
            "transformers",
        )
        host = (
            self.config.get("llm_host")
            or self.config.get("ollama_host")
        )
        model = self.config.get(
            "model",
            "microsoft/phi-2",
        )

        return LLMParser(
            provider=provider,
            host=host,
            model=model,
        )

    def process_directory(
        self,
        input_dir: str,
        progress_callback=None,
    ) -> List[Dict]:
        if not os.path.exists(input_dir):
            raise FileNotFoundError(
                f"Input directory not found: {input_dir}"
            )

        supported_extensions = (
            ".pdf",
            ".png",
            ".jpg",
            ".jpeg",
        )
        files = [
            os.path.join(
                input_dir,
                filename,
            )
            for filename in os.listdir(input_dir)
            if filename.lower().endswith(
                supported_extensions
            )
        ]

        if not files:
            self.logger.warning(
                "No supported documents found in %s",
                input_dir,
            )
            return []

        self.logger.info(
            "Found %s documents to process",
            len(files),
        )

        processed_documents = []
        for index, file_path in enumerate(files):
            try:
                if progress_callback:
                    progress_callback(
                        index,
                        len(files),
                        (
                            "Processing "
                            f"{os.path.basename(file_path)}"
                        ),
                    )

                result = self.process_single_document(
                    file_path
                )
                processed_documents.append(result)

            except Exception as exc:
                self.logger.error(
                    "Failed to process %s: %s",
                    file_path,
                    exc,
                )
                processed_documents.append(
                    {
                        "source_file": (
                            os.path.basename(
                                file_path
                            )
                        ),
                        "error": str(exc),
                        "processing_status": "failed",
                        "processing_timestamp": (
                            datetime.now().isoformat()
                        ),
                    }
                )

        try:
            csv_file = (
                self.crm.generate_csv_summary(
                    processed_documents
                )
            )
            self.logger.info(
                "Generated CSV summary: %s",
                csv_file,
            )
        except Exception as exc:
            self.logger.error(
                "Failed to generate CSV summary: %s",
                exc,
            )

        return processed_documents

    def process_single_document(
        self,
        file_path: str,
    ) -> Dict:
        filename = os.path.basename(file_path)
        start_time = datetime.now()

        self.logger.info(
            "Starting processing for %s",
            filename,
        )

        try:
            self.logger.debug(
                "Step 1: OCR extraction for %s",
                filename,
            )
            extracted_text = self.ocr.extract_text(
                file_path
            )

            if not extracted_text.strip():
                raise ValueError(
                    "No text could be extracted "
                    "from document"
                )

            self.logger.debug(
                "Step 2: LLM parsing for %s",
                filename,
            )
            parsed_data = self.llm.parse_document(
                extracted_text,
                filename,
            )

            self.logger.debug(
                "Step 3: Validation for %s",
                filename,
            )
            validated_data = (
                self.validator.validate_document(
                    parsed_data
                )
            )

            self.logger.debug(
                "Step 4: CRM submission for %s",
                filename,
            )
            submission_result = (
                self.crm.submit_document(
                    validated_data
                )
            )

            completed_at = datetime.now()
            final_result = {
                **validated_data,
                "extracted_text": extracted_text,
                "submission_result": submission_result,
                "processing_status": "completed",
                "processing_timestamp": (
                    completed_at.isoformat()
                ),
                "processing_time_seconds": (
                    completed_at - start_time
                ).total_seconds(),
            }

            self.logger.info(
                "Successfully processed %s "
                "in %.2f seconds",
                filename,
                final_result[
                    "processing_time_seconds"
                ],
            )
            return final_result

        except Exception as exc:
            error_msg = str(exc)
            self.logger.error(
                "Failed to process %s: %s",
                filename,
                error_msg,
            )

            return {
                "source_file": filename,
                "error": error_msg,
                "processing_status": "failed",
                "processing_timestamp": (
                    datetime.now().isoformat()
                ),
                "processing_time_seconds": (
                    datetime.now() - start_time
                ).total_seconds(),
            }

    def test_system_components(self) -> Dict:
        results = {
            "ocr": {
                "status": "unknown",
                "details": "",
            },
            "llm": {
                "status": "unknown",
                "details": "",
            },
            "output_directory": {
                "status": "unknown",
                "details": "",
            },
        }

        try:
            if self.ocr.test_installation():
                results["ocr"] = {
                    "status": "ok",
                    "details": (
                        "Tesseract OCR is working"
                    ),
                }
            else:
                results["ocr"] = {
                    "status": "error",
                    "details": (
                        "Tesseract OCR test failed"
                    ),
                }
        except Exception as exc:
            results["ocr"] = {
                "status": "error",
                "details": f"OCR error: {exc}",
            }

        try:
            if self.llm.test_connection():
                results["llm"] = {
                    "status": "ok",
                    "details": (
                        "LLM connection successful "
                        f"({self.llm.provider_id}: "
                        f"{self.llm.model})"
                    ),
                }
            else:
                results["llm"] = {
                    "status": "error",
                    "details": (
                        "Cannot connect to configured "
                        "LLM provider "
                        f"({self.llm.provider_id})"
                    ),
                }
        except Exception as exc:
            results["llm"] = {
                "status": "error",
                "details": f"LLM error: {exc}",
            }

        try:
            test_file = os.path.join(
                self.output_dir,
                "test_write.tmp",
            )
            with open(
                test_file,
                "w",
                encoding="utf-8",
            ) as handle:
                handle.write("test")
            os.remove(test_file)
            results["output_directory"] = {
                "status": "ok",
                "details": (
                    "Output directory writable: "
                    f"{self.output_dir}"
                ),
            }
        except Exception as exc:
            results["output_directory"] = {
                "status": "error",
                "details": (
                    f"Output directory error: {exc}"
                ),
            }

        return results

    def get_processing_statistics(
        self,
        processed_documents: List[Dict],
    ) -> Dict:
        if not processed_documents:
            return {}

        total = len(processed_documents)
        successful = sum(
            1
            for document in processed_documents
            if document.get(
                "processing_status"
            ) == "completed"
        )
        failed = total - successful

        validation_stats = (
            self.validator.get_validation_summary(
                [
                    document
                    for document
                    in processed_documents
                    if document.get(
                        "processing_status"
                    ) == "completed"
                ]
            )
        )

        submission_stats = (
            self.crm.get_submission_stats()
        )

        avg_processing_time = (
            sum(
                document.get(
                    "processing_time_seconds",
                    0,
                )
                for document
                in processed_documents
            )
            / total
        )

        return {
            "processing": {
                "total_documents": total,
                "successful": successful,
                "failed": failed,
                "success_rate": (
                    successful / total
                ),
                "average_processing_time": (
                    avg_processing_time
                ),
            },
            "validation": validation_stats,
            "submission": submission_stats,
        }

    def _setup_logging(self):
        log_dir = os.path.join(
            self.output_dir,
            "logs",
        )
        os.makedirs(log_dir, exist_ok=True)

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - "
            "%(levelname)s - %(message)s"
        )

        file_handler = logging.FileHandler(
            os.path.join(
                log_dir,
                (
                    "pipeline_"
                    f"{datetime.now().strftime('%Y%m%d')}"
                    ".log"
                ),
            )
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        self.logger.setLevel(logging.DEBUG)

    def update_config(
        self,
        new_config: Dict,
    ):
        self.config.update(new_config)

        if "tesseract_path" in new_config:
            self.ocr = OCRProcessor(
                tesseract_path=self.config[
                    "tesseract_path"
                ]
            )

        llm_keys = {
            "llm_provider",
            "llm_host",
            "ollama_host",
            "model",
        }
        if llm_keys.intersection(new_config):
            self.llm = self._build_llm()
