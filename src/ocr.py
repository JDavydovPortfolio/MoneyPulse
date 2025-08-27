import pytesseract
import cv2
import numpy as np
from pdf2image import convert_from_path
from PIL import Image
import re
import logging
import os

class OCRProcessor:
    """Handles text extraction from various document formats."""
    
    def __init__(self, tesseract_path=None):
        """Initialize OCR processor with optional tesseract path."""
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        elif os.name == 'nt':  # Windows
            # Try common Windows installation paths
            possible_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    break
        
        self.logger = logging.getLogger(__name__)
    
    def extract_text(self, file_path):
        """Extract text from PDF, PNG, or JPG files."""
        try:
            file_extension = file_path.lower().split('.')[-1]
            
            if file_extension == 'pdf':
                return self._extract_from_pdf(file_path)
            elif file_extension in ['png', 'jpg', 'jpeg']:
                return self._extract_from_image(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")
                
        except Exception as e:
            self.logger.error(f"OCR extraction failed for {file_path}: {str(e)}")
            raise
    
    def _extract_from_pdf(self, pdf_path):
        """Convert PDF to images and extract text."""
        try:
            pages = convert_from_path(pdf_path, dpi=300)
            full_text = ""
            
            for page_num, page in enumerate(pages, 1):
                page_text = self._extract_from_pil_image(page)
                full_text += f"\n--- Page {page_num} ---\n{page_text}"
            
            return self._clean_text(full_text)
        except Exception as e:
            self.logger.error(f"PDF processing failed: {str(e)}")
            raise
    
    def _extract_from_image(self, image_path):
        """Extract text from image file."""
        try:
            image = Image.open(image_path)
            return self._clean_text(self._extract_from_pil_image(image))
        except Exception as e:
            self.logger.error(f"Image processing failed: {str(e)}")
            raise
    
    def _extract_from_pil_image(self, image):
        """Extract text from PIL Image object with preprocessing."""
        try:
            # Convert to OpenCV format for preprocessing
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Image preprocessing for better OCR accuracy
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Noise reduction
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(denoised)
            
            # Use pytesseract with custom config for better accuracy
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz .,()-@#$%&*+:;=?'
            text = pytesseract.image_to_string(enhanced, config=custom_config)
            
            return text
        except Exception as e:
            self.logger.error(f"OCR processing failed: {str(e)}")
            raise
    
    def _clean_text(self, text):
        """Clean and normalize extracted text."""
        if not text:
            return ""
        
        # Remove excessive whitespace and line breaks
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r' +', ' ', text)
        
        # Remove common OCR artifacts
        text = re.sub(r'[^\w\s\-.,()/@#$%&*+:;=?]', ' ', text)
        
        # Fix common OCR mistakes in numeric contexts
        # Only apply these substitutions in contexts that look like numbers
        text = re.sub(r'\bO(\d)', r'0\1', text)  # O followed by digit
        text = re.sub(r'(\d)O\b', r'\g<1>0', text)  # digit followed by O
        text = re.sub(r'\bl(\d)', r'1\1', text)  # l followed by digit
        text = re.sub(r'(\d)l\b', r'\g<1>1', text)  # digit followed by l
        
        return text.strip()
    
    def test_installation(self):
        """Test if Tesseract is properly installed."""
        try:
            # Create a simple test image
            test_image = Image.new('RGB', (200, 50), color='white')
            # This would normally add text to test, but for simplicity:
            test_text = pytesseract.image_to_string(test_image)
            return True
        except Exception as e:
            self.logger.error(f"Tesseract test failed: {str(e)}")
            return False