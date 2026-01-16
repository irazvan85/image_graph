"""
Base analyzer interface
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from pathlib import Path


class BaseAnalyzer(ABC):
    """Base class for image analyzers"""
    
    def __init__(self, config):
        self.config = config
        self.enabled = config.get(f"analyzers.{self.__class__.__name__.lower().replace('analyzer', '')}.enabled", True)
    
    @abstractmethod
    async def analyze(self, image_path: Path) -> Dict[str, Any]:
        """Analyze image and return results"""
        pass
    
    def is_enabled(self) -> bool:
        """Check if analyzer is enabled"""
        return self.enabled
