"""
ImageGraph Backend - FastAPI Server
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import os
from pathlib import Path

from pathlib import Path
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from services.scanner import ImageScanner
from services.processor import ImageProcessor
from services.graph_builder import GraphBuilder
from services.graph_exporter import GraphExporter
from database import Database
from config import Config

app = FastAPI(title="ImageGraph API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
config = Config()
db = Database(config)
scanner = ImageScanner(config)
processor = ImageProcessor(config, db)
graph_builder = GraphBuilder(config, db)
exporter = GraphExporter(config, db)

# Global state for progress tracking
processing_state = {
    "status": "idle",  # idle, scanning, processing, completed, error
    "progress": 0,
    "total": 0,
    "current_file": None,
    "error": None
}


class ScanRequest(BaseModel):
    folder_path: str
    file_list: Optional[List[str]] = None


# GraphFilters removed - using query parameters instead


@app.on_event("startup")
async def startup():
    """Initialize database and services on startup"""
    await db.initialize()
    await processor.initialize()


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    await db.close()


@app.post("/api/scan")
async def scan_folder(request: ScanRequest, background_tasks: BackgroundTasks):
    """Start scanning and processing a folder"""
    global processing_state
    
    if processing_state["status"] in ["scanning", "processing"]:
        raise HTTPException(status_code=400, detail="Processing already in progress")
    
    folder_path = Path(request.folder_path)
    if not folder_path.exists():
        raise HTTPException(status_code=404, detail="Folder not found")
    
    processing_state.update({
        "status": "scanning",
        "progress": 0,
        "total": 0,
        "current_file": None,
        "error": None
    })
    
    # Start background processing
    background_tasks.add_task(process_folder, folder_path, request.file_list)
    
    return {"status": "started", "message": "Processing started"}


async def process_folder(folder_path: Path, file_list: Optional[List[str]]):
    """Background task to process folder"""
    global processing_state
    
    try:
        # Scan for images
        processing_state["status"] = "scanning"
        images = await scanner.scan_folder(folder_path, file_list)
        
        processing_state.update({
            "status": "processing",
            "total": len(images),
            "progress": 0
        })
        
        # Process images
        for i, image_path in enumerate(images):
            processing_state["current_file"] = str(image_path)
            processing_state["progress"] = i + 1
            
            try:
                await processor.process_image(image_path)
            except Exception as e:
                print(f"Error processing {image_path}: {e}")
                continue
        
        # Build graph
        await graph_builder.build_graph()
        
        processing_state.update({
            "status": "completed",
            "progress": len(images),
            "current_file": None
        })
        
    except Exception as e:
        processing_state.update({
            "status": "error",
            "error": str(e)
        })


@app.get("/api/progress")
async def get_progress():
    """Get current processing progress"""
    return processing_state


@app.post("/api/cancel")
async def cancel_processing():
    """Cancel current processing"""
    global processing_state
    if processing_state["status"] in ["scanning", "processing"]:
        processing_state["status"] = "cancelled"
        return {"status": "cancelled"}
    return {"status": "not_processing"}


@app.get("/api/graph")
async def get_graph(
    min_confidence: Optional[float] = None,
    min_similarity: Optional[float] = None,
    search_query: Optional[str] = None,
    concept_types: Optional[str] = None
):
    """Get the knowledge graph with optional filters"""
    filters_dict = {}
    if min_confidence is not None:
        filters_dict["min_confidence"] = min_confidence
    if min_similarity is not None:
        filters_dict["min_similarity"] = min_similarity
    if search_query:
        filters_dict["search_query"] = search_query
    if concept_types:
        filters_dict["concept_types"] = concept_types.split(",")
    
    graph = await graph_builder.get_graph(filters_dict)
    return graph


@app.get("/api/image/{image_id}")
async def get_image_metadata(image_id: str):
    """Get metadata and thumbnail for an image"""
    metadata = await db.get_image_metadata(image_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Get thumbnail path
    thumbnail_path = processor.get_thumbnail_path(image_id)
    if thumbnail_path and thumbnail_path.exists():
        return {
            "metadata": metadata,
            "thumbnail_url": f"/api/thumbnail/{image_id}"
        }
    
    return {"metadata": metadata}


@app.get("/api/thumbnail/{image_id}")
async def get_thumbnail(image_id: str):
    """Serve thumbnail image"""
    thumbnail_path = processor.get_thumbnail_path(image_id)
    if thumbnail_path and thumbnail_path.exists():
        return FileResponse(thumbnail_path)
    raise HTTPException(status_code=404, detail="Thumbnail not found")


@app.post("/api/rescan")
async def rescan_folder(request: ScanRequest, background_tasks: BackgroundTasks):
    """Rescan folder and only process new/changed files"""
    folder_path = Path(request.folder_path)
    if not folder_path.exists():
        raise HTTPException(status_code=404, detail="Folder not found")
    
    # Get list of already processed files
    processed_files = await db.get_processed_files()
    
    # Filter out already processed files
    all_images = await scanner.scan_folder(folder_path, request.file_list)
    new_images = [img for img in all_images if str(img) not in processed_files]
    
    if not new_images:
        return {"status": "no_changes", "message": "No new or changed files"}
    
    processing_state.update({
        "status": "scanning",
        "progress": 0,
        "total": len(new_images),
        "current_file": None,
        "error": None
    })
    
    background_tasks.add_task(process_folder, folder_path, [str(img) for img in new_images])
    
    return {"status": "started", "message": f"Processing {len(new_images)} new/changed files"}


@app.get("/api/export")
async def export_graph(format: str = "json"):
    """Export graph in specified format"""
    if format == "json":
        graph = await graph_builder.get_graph({})
        return JSONResponse(content=graph)
    elif format == "graphml":
        graphml = await exporter.export_graphml()
        return JSONResponse(content={"graphml": graphml})
    elif format == "cypher":
        cypher = await exporter.export_cypher()
        return JSONResponse(content={"cypher": cypher})
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")


@app.get("/api/config")
async def get_config():
    """Get analyzer configuration and status"""
    import os
    
    # Get analyzer configurations
    analyzers_status = {
        "ocr": {
            "enabled": config.get("analyzers.ocr.enabled", False),
            "engine": config.get("analyzers.ocr.engine", "tesseract")
        },
        "captioning": {
            "enabled": config.get("analyzers.captioning.enabled", False),
            "model": config.get("analyzers.captioning.model", "blip-base")
        },
        "embeddings": {
            "enabled": config.get("analyzers.embeddings.enabled", False),
            "model": config.get("analyzers.embeddings.model", "clip-ViT-B/32")
        },
        "object_detection": {
            "enabled": config.get("analyzers.object_detection.enabled", False),
            "model": config.get("analyzers.object_detection.model", "yolov8n")
        },
        "face_detection": {
            "enabled": config.get("analyzers.face_detection.enabled", False)
        }
    }
    
    # Get LLM configuration
    llm_enabled = config.get("llm.enabled", False)
    llm_api_key = config.get("llm.api_key") or os.getenv("LLM_API_KEY")
    llm_active = llm_enabled and bool(llm_api_key)
    
    llm_config = {
        "enabled": llm_enabled,
        "active": llm_active,
        "provider": config.get("llm.provider", "openai"),
        "model": config.get("llm.model", "gpt-4-vision-preview"),
        "has_api_key": bool(llm_api_key)
    }
    
    return {
        "analyzers": analyzers_status,
        "llm": llm_config
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
