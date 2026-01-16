"""
Image folder scanner
"""
from pathlib import Path
from typing import List, Optional
import asyncio


class ImageScanner:
    """Scans folder for images"""
    
    SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif'}
    
    def __init__(self, config):
        self.config = config
    
    async def scan_folder(self, folder_path: Path, file_list: Optional[List[str]] = None) -> List[Path]:
        """Scan folder for images"""
        if file_list:
            # Use provided file list
            images = []
            for file_path in file_list:
                path = Path(file_path)
                if path.suffix.lower() in self.SUPPORTED_EXTENSIONS and path.exists():
                    images.append(path)
            return images
        
        # Scan folder recursively
        images = []
        folder_path = Path(folder_path)
        
        if not folder_path.exists():
            return images
        
        # Use asyncio to scan in background
        loop = asyncio.get_event_loop()
        images = await loop.run_in_executor(
            None,
            self._scan_sync,
            folder_path
        )
        
        return images
    
    def _scan_sync(self, folder_path: Path) -> List[Path]:
        """Synchronous folder scanning"""
        images = []
        for ext in self.SUPPORTED_EXTENSIONS:
            images.extend(folder_path.rglob(f"*{ext}"))
            images.extend(folder_path.rglob(f"*{ext.upper()}"))
        return sorted(set(images))
