"""
Optional LLM analyzer for enhanced entity extraction
"""
from pathlib import Path
from typing import Dict, Any, List
import base64
import os

from .base import BaseAnalyzer


class LLMAnalyzer(BaseAnalyzer):
    """LLM-based enhanced analysis"""
    
    def __init__(self, config):
        super().__init__(config)
        self.api_key = config.get("llm.api_key") or os.getenv("LLM_API_KEY")
        self.provider = config.get("llm.provider", "openai")
        self.model = config.get("llm.model", "gpt-4-vision-preview")
        self.use_for_entities = config.get("llm.use_for_entities", True)
        self.use_for_relations = config.get("llm.use_for_relations", True)
        self.client = None
    
    async def initialize(self):
        """Initialize LLM client"""
        if not self.is_enabled() or not self.api_key:
            return
        
        if self.provider == "openai":
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except ImportError:
                print("Warning: openai package not installed")
                self.enabled = False
    
    async def analyze(self, image_path: Path, caption: str = "", ocr_text: str = "") -> Dict[str, Any]:
        """Enhanced analysis using LLM"""
        if not self.is_enabled() or not self.client:
            return {}
        
        await self.initialize()
        
        try:
            # Encode image
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode()
            
            # Build prompt
            prompt = self._build_prompt(caption, ocr_text)
            
            # Call LLM
            response = await self._call_llm(image_data, prompt)
            
            return {
                "llm_entities": response.get("entities", []),
                "llm_relations": response.get("relations", []),
                "llm_description": response.get("description", "")
            }
        except Exception as e:
            print(f"Error in LLM analysis for {image_path}: {e}")
            return {}
    
    def _build_prompt(self, caption: str, ocr_text: str) -> str:
        """Build prompt for LLM"""
        prompt = """Analyze this image and extract:
1. Entities: objects, people, places, organizations mentioned or visible
2. Relations: relationships between entities (e.g., "person holding object", "event happening")
3. Description: a detailed description of the scene

"""
        if caption:
            prompt += f"Caption: {caption}\n"
        if ocr_text:
            prompt += f"OCR Text: {ocr_text}\n"
        
        prompt += "\nReturn JSON with keys: entities (array), relations (array), description (string)"
        return prompt
    
    async def _call_llm(self, image_data: str, prompt: str) -> Dict[str, Any]:
        """Call LLM API"""
        import json
        
        if self.provider == "openai":
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                            }
                        ]
                    }
                ],
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            try:
                return json.loads(content)
            except:
                return {"description": content}
