"""
Image processor - orchestrates all analyzers
"""
from pathlib import Path
from typing import Dict, Any
from PIL import Image
import hashlib
import pickle
import numpy as np
from datetime import datetime

from services.analyzers.caption_analyzer import CaptionAnalyzer
from services.analyzers.ocr_analyzer import OCRAnalyzer
from services.analyzers.embedding_analyzer import EmbeddingAnalyzer
from services.analyzers.llm_analyzer import LLMAnalyzer


class ImageProcessor:
    """Processes images through all analyzers"""
    
    def __init__(self, config, database):
        self.config = config
        self.db = database
        
        # Initialize analyzers
        self.caption_analyzer = CaptionAnalyzer(config)
        self.ocr_analyzer = OCRAnalyzer(config)
        self.embedding_analyzer = EmbeddingAnalyzer(config)
        self.llm_analyzer = LLMAnalyzer(config)
        
        # Thumbnail directory
        self.thumbnails_path = Path(config.thumbnails_path)
        self.thumbnails_path.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self):
        """Initialize all analyzers"""
        await self.caption_analyzer.initialize()
        await self.ocr_analyzer.initialize()
        await self.embedding_analyzer.initialize()
        await self.llm_analyzer.initialize()
    
    async def process_image(self, image_path: Path):
        """Process a single image through all analyzers"""
        try:
            # Get image metadata
            image_data = await self._get_image_metadata(image_path)
            image_id = await self.db.save_image(image_data)
            
            # Run analyzers
            caption_result = await self.caption_analyzer.analyze(image_path)
            ocr_result = await self.ocr_analyzer.analyze(image_path)
            embedding_result = await self.embedding_analyzer.analyze(image_path)
            
            # LLM analysis (if enabled and has caption/OCR)
            llm_result = {}
            if self.llm_analyzer.is_enabled():
                llm_result = await self.llm_analyzer.analyze(
                    image_path,
                    caption=caption_result.get("caption", ""),
                    ocr_text=ocr_result.get("ocr_text", "")
                )
            
            # Extract tags from caption
            tags = self._extract_tags(caption_result.get("caption", ""))
            if llm_result.get("llm_entities"):
                tags.extend([e.get("value", "") for e in llm_result["llm_entities"]])
            
            # Save metadata
            metadata = {
                "caption": caption_result.get("caption"),
                "tags": tags,
                "ocr_text": ocr_result.get("ocr_text"),
                "ocr_entities": ocr_result.get("ocr_entities", [])
            }
            await self.db.save_image_metadata(image_id, metadata)
            
            # Save embedding
            if embedding_result.get("embedding") is not None:
                embedding = embedding_result["embedding"]
                embedding_bytes = pickle.dumps(embedding.astype(np.float32))
                embedding_id = await self.db.save_embedding(image_id, embedding_bytes)
                
                # Update metadata with embedding_id
                metadata["embedding_id"] = embedding_id
                await self.db.save_image_metadata(image_id, metadata)
            
            # Generate thumbnail
            thumbnail_path = self._generate_thumbnail(image_path, image_id)
            if thumbnail_path:
                image_data["thumbnail_path"] = str(thumbnail_path)
                await self.db.save_image(image_data)
            
        except Exception as e:
            print(f"Error processing image {image_path}: {e}")
            raise
    
    async def _get_image_metadata(self, image_path: Path) -> Dict[str, Any]:
        """Get basic image metadata"""
        try:
            image = Image.open(image_path)
            stat = image_path.stat()
            
            # Calculate file hash
            file_hash = self._calculate_hash(image_path)
            
            return {
                "file_path": str(image_path.absolute()),
                "file_hash": file_hash,
                "created_time": stat.st_ctime,
                "modified_time": stat.st_mtime,
                "width": image.width,
                "height": image.height,
                "file_size": stat.st_size
            }
        except Exception as e:
            print(f"Error getting metadata for {image_path}: {e}")
            return {
                "file_path": str(image_path.absolute()),
                "file_hash": None,
                "created_time": datetime.now().timestamp(),
                "modified_time": datetime.now().timestamp(),
                "width": None,
                "height": None,
                "file_size": None
            }
    
    def _calculate_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _extract_tags(self, caption: str) -> list:
        """Extract tags from caption"""
        if not caption:
            return []
        
        # Simple noun phrase extraction
        import re
        # Remove common stop words
        stop_words = {'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                     'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                     'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'}
        
        # Extract words (simple approach)
        words = re.findall(r'\b[a-zA-Z]+\b', caption.lower())
        tags = [w for w in words if w not in stop_words and len(w) > 2]
        
        # Remove duplicates and return top tags
        return list(set(tags))[:15]
    
    def _generate_thumbnail(self, image_path: Path, image_id: str) -> Path:
        """Generate thumbnail for image"""
        try:
            max_size = self.config.get("ui.max_thumbnail_size", 200)
            image = Image.open(image_path)
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            thumbnail_path = self.thumbnails_path / f"{image_id}.jpg"
            image.save(thumbnail_path, "JPEG", quality=85)
            return thumbnail_path
        except Exception as e:
            print(f"Error generating thumbnail for {image_path}: {e}")
            return None
    
    def get_thumbnail_path(self, image_id: str) -> Path:
        """Get thumbnail path for image"""
        return self.thumbnails_path / f"{image_id}.jpg"
