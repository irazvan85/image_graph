"""
OCR analyzer using Tesseract or EasyOCR
"""
from pathlib import Path
from typing import Dict, Any, List
import asyncio
import re

from .base import BaseAnalyzer


class OCRAnalyzer(BaseAnalyzer):
    """OCR text extraction"""
    
    def __init__(self, config):
        super().__init__(config)
        self.engine = config.get("analyzers.ocr.engine", "tesseract")
        self.tesseract = None
        self.easyocr = None
    
    async def initialize(self):
        """Initialize OCR engine"""
        if not self.is_enabled():
            return
        
        if self.engine == "tesseract":
            try:
                import pytesseract
                self.tesseract = pytesseract
            except ImportError:
                print("Warning: pytesseract not available")
                self.enabled = False
        elif self.engine == "easyocr":
            try:
                import easyocr
                loop = asyncio.get_event_loop()
                self.easyocr = await loop.run_in_executor(
                    None,
                    lambda: easyocr.Reader(['en'])
                )
            except Exception as e:
                print(f"Warning: EasyOCR not available: {e}")
                self.enabled = False
    
    async def analyze(self, image_path: Path) -> Dict[str, Any]:
        """Extract OCR text and entities"""
        if not self.is_enabled():
            return {}
        
        await self.initialize()
        
        try:
            if self.engine == "tesseract" and self.tesseract:
                loop = asyncio.get_event_loop()
                text = await loop.run_in_executor(
                    None,
                    self._extract_tesseract,
                    image_path
                )
            elif self.engine == "easyocr" and self.easyocr:
                loop = asyncio.get_event_loop()
                text = await loop.run_in_executor(
                    None,
                    self._extract_easyocr,
                    image_path
                )
            else:
                return {}
            
            if not text:
                return {}
            
            # Extract entities
            entities = self._extract_entities(text)
            
            return {
                "ocr_text": text,
                "ocr_entities": entities
            }
        except Exception as e:
            print(f"Error in OCR for {image_path}: {e}")
            return {}
    
    def _extract_tesseract(self, image_path: Path) -> str:
        """Extract text using Tesseract"""
        from PIL import Image
        image = Image.open(image_path)
        return self.tesseract.image_to_string(image)
    
    def _extract_easyocr(self, image_path: Path) -> str:
        """Extract text using EasyOCR"""
        results = self.easyocr.readtext(str(image_path))
        return " ".join([result[1] for result in results])
    
    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities from OCR text"""
        entities = []
        
        # Extract dates
        date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'
        dates = re.findall(date_pattern, text)
        for date in dates:
            entities.append({"type": "date", "value": date})
        
        # Extract amounts/money
        amount_pattern = r'\$\d+\.?\d*|\d+\.?\d*\s*(?:dollars?|USD|EUR|GBP)'
        amounts = re.findall(amount_pattern, text, re.IGNORECASE)
        for amount in amounts:
            entities.append({"type": "amount", "value": amount})
        
        # Extract email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        for email in emails:
            entities.append({"type": "email", "value": email})
        
        # Extract keywords (capitalized words, likely proper nouns)
        keywords = re.findall(r'\b[A-Z][a-z]+\b', text)
        for keyword in set(keywords):
            if len(keyword) > 2:
                entities.append({"type": "keyword", "value": keyword})
        
        return entities
