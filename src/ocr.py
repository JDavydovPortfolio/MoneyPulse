#!/usr/bin/env python3
"""OCR extraction for PDFs and supported image formats."""

import logging
from pathlib import Path

import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_path

logger = logging.getLogger(__name__)
SUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}


class OCRProcessor:
    """Handle text extraction from documents using Tesseract OCR."""

    def __init__(self, tesseract_path: str = None):
        self.logger = logging.getLogger(__name__)
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path

    def extract_text(self, file_path: str) -> str:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Input file not found: {path}")
        if not path.is_file():
            raise ValueError(f"Input path is not a file: {path}")
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type '{path.suffix or '<none>'}'. "
                "Supported types: PDF, PNG, JPG, JPEG"
            )
        try:
            if path.suffix.lower() == ".pdf":
                return _extract_from_pdf(path)
            return _extract_from_image(path)
        except pytesseract.TesseractNotFoundError as exc:
            raise RuntimeError(
                "Tesseract OCR is not installed or is not on PATH. "
                "Install Tesseract or configure tesseract_path."
            ) from exc
        except Exception as exc:
            self.logger.error("Failed to extract text from %s: %s", path, exc)
            raise

    def test_installation(self) -> bool:
        try:
            version = pytesseract.get_tesseract_version()
            self.logger.info("Tesseract OCR version: %s", version)
            return True
        except Exception as exc:
            self.logger.error("Tesseract OCR test failed: %s", exc)
            return False


def extract_text(file_path: str) -> str:
    return OCRProcessor().extract_text(file_path)


def _extract_from_pdf(pdf_path: Path) -> str:
    try:
        images = convert_from_path(pdf_path)
    except Exception as exc:
        message = str(exc)
        if "poppler" in message.lower() or "pdfinfo" in message.lower():
            raise RuntimeError(
                "PDF rendering failed. Ensure Poppler is installed and available on PATH."
            ) from exc
        raise

    extracted_text = []
    for image in images:
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        processed = _preprocess_image(cv_image)
        extracted_text.append(pytesseract.image_to_string(processed))
    return "\n\n".join(extracted_text)


def _extract_from_image(image_path: Path) -> str:
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Failed to load image: {image_path}")
    processed = _preprocess_image(image)
    return pytesseract.image_to_string(processed)


def _preprocess_image(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    return cv2.medianBlur(thresh, 3)
