#!/usr/bin/env python3
"""
OCR Module
Handles text extraction from PDFs and images using Tesseract OCR
"""

import logging
from pathlib import Path

import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_path

logger = logging.getLogger(__name__)

class OCRProcessor:
    """Handles text extraction from documents using OCR."""
    
    def __init__(self, tesseract_path: str = None):
        """Initialize the OCR processor with an optional tesseract path."""
        self.logger = logging.getLogger(__name__)
        
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
    
    def extract_text(self, file_path: str) -> str:
        """
        Extract text from a document file (PDF or image).

        Args:
            file_path: Path to the document file

        Returns:
            Extracted text as string
        """
        try:
            file_path = Path(file_path)

            if file_path.suffix.lower() == '.pdf':
                return globals()['_extract_from_pdf'](file_path)
            else:
                return globals()['_extract_from_image'](file_path)

        except Exception as e:
            self.logger.error(f"Failed to extract text from {file_path}: {e}")
            raise
    
    def test_installation(self) -> bool:
        """Test if Tesseract OCR is properly installed and working."""
        try:
            version = pytesseract.get_tesseract_version()
            self.logger.info(f"Tesseract OCR version: {version}")
            return True
        except Exception as e:
            self.logger.error(f"Tesseract OCR test failed: {e}")
            return False

def extract_text(file_path: str) -> str:
    """
    Extract text from a document file (PDF or image).
    
    This is a convenience function that uses OCRProcessor internally.
    For more control, use OCRProcessor directly.
    """
    processor = OCRProcessor()
    return processor.extract_text(file_path)

def _extract_from_pdf(pdf_path: Path) -> str:
    """Extract text from the PDF file."""
    try:
        images = convert_from_path(pdf_path)

        extracted_text = []
        for image in images:
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            processed = _preprocess_image(cv_image)

            text = pytesseract.image_to_string(processed)
            extracted_text.append(text)

        return "\n\n".join(extracted_text)

    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        raise

def _extract_from_image(image_path: Path) -> str:
    """Extract text from an image file."""
    try:
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Failed to load image: {image_path}")

        processed = _preprocess_image(image)

        return pytesseract.image_to_string(processed)

    except Exception as e:
        logger.error(f"Image extraction error: {e}")
        raise

def _preprocess_image(image: np.ndarray) -> np.ndarray:
    """Preprocess image for better OCR results."""
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

        denoised = cv2.medianBlur(thresh, 3)

        return denoised

    except Exception as e:
        logger.error(f"Image preprocessing error: {e}")
        raise
