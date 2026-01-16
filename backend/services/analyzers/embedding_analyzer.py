"""
Image embedding analyzer using CLIP
"""
import torch
import numpy as np
from pathlib import Path
from typing import Dict, Any
import asyncio
from PIL import Image

from .base import BaseAnalyzer


class EmbeddingAnalyzer(BaseAnalyzer):
    """CLIP-based image embeddings"""
    
    def __init__(self, config):
        super().__init__(config)
        self.model = None
        self.preprocess = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_name = config.get("analyzers.embeddings.model", "clip-ViT-B/32")
    
    async def initialize(self):
        """Initialize CLIP model"""
        if not self.is_enabled():
            return
        
        if self.model is None:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._load_model)
    
    def _load_model(self):
        """Load CLIP model"""
        try:
            import clip
            
            model_name_map = {
                "clip-ViT-B/32": "ViT-B/32",
                "clip-ViT-L/14": "ViT-L/14"
            }
            clip_model_name = model_name_map.get(self.model_name, "ViT-B/32")
            
            self.model, self.preprocess = clip.load(clip_model_name, device=self.device)
            self.model.eval()
        except ImportError:
            # Try open_clip as fallback
            try:
                import open_clip
                model_name_map = {
                    "clip-ViT-B/32": ("ViT-B-32", "openai"),
                    "clip-ViT-L/14": ("ViT-L-14", "openai")
                }
                model_name, pretrained = model_name_map.get(self.model_name, ("ViT-B-32", "openai"))
                
                self.model, _, self.preprocess = open_clip.create_model_and_transforms(
                    model_name, pretrained=pretrained, device=self.device
                )
                self.model.eval()
            except Exception as e:
                print(f"Warning: Could not load CLIP model: {e}")
                self.enabled = False
    
    async def analyze(self, image_path: Path) -> Dict[str, Any]:
        """Generate embedding for image"""
        if not self.is_enabled():
            return {}
        
        await self.initialize()
        
        if self.model is None:
            return {}
        
        try:
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(None, self._generate_embedding, image_path)
            return {"embedding": embedding}
        except Exception as e:
            print(f"Error generating embedding for {image_path}: {e}")
            return {}
    
    def _generate_embedding(self, image_path: Path) -> np.ndarray:
        """Generate embedding synchronously"""
        image = Image.open(image_path).convert('RGB')
        image_tensor = self.preprocess(image).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            image_features = self.model.encode_image(image_tensor)
            # Normalize
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        
        return image_features.cpu().numpy().flatten()
