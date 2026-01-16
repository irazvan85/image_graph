"""
Configuration management
"""
import yaml
from pathlib import Path
from typing import Dict, Any
import os


class Config:
    """Configuration manager"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._apply_env_overrides()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            # Return default config
            return self._get_default_config()
        
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "processing": {
                "batch_size": 10,
                "max_workers": 4,
                "similarity_threshold": 0.7,
                "confidence_threshold": 0.3,
                "image_similarity_threshold": 0.85
            },
            "analyzers": {
                "ocr": {"enabled": True, "engine": "tesseract"},
                "captioning": {"enabled": True, "model": "blip-base"},
                "embeddings": {"enabled": True, "model": "clip-ViT-B/32"}
            },
            "storage": {
                "database_path": "data/imagegraph.db",
                "vector_index_path": "data/faiss_index",
                "thumbnails_path": "data/thumbnails"
            }
        }
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides"""
        # LLM API key
        if os.getenv("LLM_API_KEY"):
            if "llm" not in self.config:
                self.config["llm"] = {}
            self.config["llm"]["api_key"] = os.getenv("LLM_API_KEY")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value
    
    @property
    def similarity_threshold(self) -> float:
        return self.get("processing.similarity_threshold", 0.7)
    
    @property
    def confidence_threshold(self) -> float:
        return self.get("processing.confidence_threshold", 0.3)
    
    @property
    def image_similarity_threshold(self) -> float:
        return self.get("processing.image_similarity_threshold", 0.85)
    
    @property
    def database_path(self) -> str:
        return self.get("storage.database_path", "data/imagegraph.db")
    
    @property
    def vector_index_path(self) -> str:
        return self.get("storage.vector_index_path", "data/faiss_index")
    
    @property
    def thumbnails_path(self) -> str:
        return self.get("storage.thumbnails_path", "data/thumbnails")
