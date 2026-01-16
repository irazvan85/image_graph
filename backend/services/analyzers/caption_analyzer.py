"""
Image captioning analyzer using BLIP
"""
import torch
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
from pathlib import Path
from typing import Dict, Any
import asyncio

from .base import BaseAnalyzer


class CaptionAnalyzer(BaseAnalyzer):
    """BLIP-based image captioning"""
    
    def __init__(self, config):
        super().__init__(config)
        self.model = None
        self.processor = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_name = config.get("analyzers.captioning.model", "blip-base")
    
    async def initialize(self):
        """Initialize model (lazy loading)"""
        if not self.is_enabled():
            return
        
        if self.model is None:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._load_model)
    
    def _load_model(self):
        """Load BLIP model"""
        try:
            model_name_map = {
                "blip-base": "Salesforce/blip-image-captioning-base",
                "blip-large": "Salesforce/blip-image-captioning-large"
            }
            model_name = model_name_map.get(self.model_name, model_name_map["blip-base"])
            
            self.processor = BlipProcessor.from_pretrained(model_name)
            self.model = BlipForConditionalGeneration.from_pretrained(model_name).to(self.device)
            self.model.eval()
        except Exception as e:
            print(f"Warning: Could not load BLIP model: {e}")
            self.enabled = False
    
    async def analyze(self, image_path: Path) -> Dict[str, Any]:
        """Generate caption for image"""
        if not self.is_enabled():
            return {}
        
        await self.initialize()
        
        if self.model is None:
            return {}
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._generate_caption, image_path)
            return {"caption": result}
        except Exception as e:
            print(f"Error generating caption for {image_path}: {e}")
            return {}
    
    def _generate_caption(self, image_path: Path) -> str:
        """Generate caption synchronously"""
        image = Image.open(image_path).convert('RGB')
        
        inputs = self.processor(image, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            out = self.model.generate(**inputs, max_length=50)
        
        caption = self.processor.decode(out[0], skip_special_tokens=True)
        return caption
