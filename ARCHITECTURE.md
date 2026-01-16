# ImageGraph Architecture

## System Overview

ImageGraph is a full-stack application that builds knowledge graphs from image collections. It uses modern ML models for content understanding and provides an interactive visualization interface.

## Components

### Backend (FastAPI)

#### Core Services

1. **ImageScanner** (`services/scanner.py`)
   - Recursively scans folders for images
   - Supports multiple image formats
   - Returns list of image paths

2. **ImageProcessor** (`services/processor.py`)
   - Orchestrates all analyzers
   - Manages image metadata extraction
   - Generates thumbnails
   - Saves results to database

3. **GraphBuilder** (`services/graph_builder.py`)
   - Builds knowledge graph from processed images
   - Normalizes concepts
   - Creates edges based on relationships
   - Computes similarity between images

4. **GraphExporter** (`services/graph_exporter.py`)
   - Exports graph in multiple formats
   - JSON, GraphML, Neo4j Cypher

#### Analyzers

1. **CaptionAnalyzer** (BLIP)
   - Generates natural language captions
   - Extracts semantic content

2. **OCRAnalyzer** (Tesseract/EasyOCR)
   - Extracts text from images
   - Identifies entities (dates, amounts, emails)

3. **EmbeddingAnalyzer** (CLIP)
   - Generates vector embeddings
   - Enables similarity search

4. **LLMAnalyzer** (Optional)
   - Enhanced entity extraction
   - Relationship identification
   - Requires API key

#### Database Layer

- **SQLite** for metadata storage
- Tables: images, image_metadata, concepts, edges, embeddings
- Efficient indexing for fast queries

### Frontend (React + Vite)

#### Components

1. **FolderSelector**: Initial folder selection
2. **GraphView**: Cytoscape.js visualization
3. **Filters**: Confidence/similarity thresholds, search
4. **ProgressBar**: Processing status
5. **ImageDetail**: Side panel with image metadata

## Data Flow

```
User selects folder
    ↓
POST /api/scan
    ↓
Background task starts
    ↓
For each image:
    ├─→ CaptionAnalyzer → caption
    ├─→ OCRAnalyzer → text + entities
    ├─→ EmbeddingAnalyzer → vector
    └─→ LLMAnalyzer (optional) → enhanced entities
    ↓
Save to database
    ↓
Build graph:
    ├─→ Extract tags from captions
    ├─→ Normalize concepts
    ├─→ Create Image→Concept edges
    ├─→ Create Concept→Concept edges (co-occurrence)
    └─→ Create Image→Image edges (similarity)
    ↓
GET /api/graph
    ↓
Frontend renders with Cytoscape.js
```

## Graph Structure

### Nodes

- **Image Nodes**: 
  - ID: hash of file path
  - Attributes: path, dimensions, timestamp, thumbnail

- **Concept Nodes**:
  - ID: hash of normalized label
  - Attributes: label, normalized_label, type (tag/entity/text_entity)

### Edges

- **Image→Concept**:
  - Weight: confidence score (0-1)
  - Source: caption, ocr, detection

- **Concept→Concept**:
  - Weight: co-occurrence count (decayed)
  - Represents concepts appearing together

- **Image→Image**:
  - Similarity: cosine similarity of embeddings (0-1)
  - Only created if similarity >= threshold

## Performance Considerations

1. **Background Processing**: Non-blocking image analysis
2. **Caching**: Results stored in database, incremental updates
3. **Batch Processing**: Configurable batch sizes
4. **GPU Acceleration**: Optional CUDA support for faster ML inference
5. **Thumbnail Caching**: Pre-generated thumbnails for fast display

## Security & Privacy

- All processing happens locally
- No images sent to external services (unless LLM mode enabled)
- LLM mode is opt-in and clearly indicated
- Database stored locally

## Extensibility

### Adding New Analyzers

1. Extend `BaseAnalyzer` in `services/analyzers/base.py`
2. Implement `analyze(image_path)` method
3. Register in `ImageProcessor`

### Adding New Export Formats

1. Add method to `GraphExporter`
2. Add endpoint in `main.py`
3. Add UI button in frontend

### Custom Graph Algorithms

Extend `GraphBuilder` to add:
- Community detection
- Centrality measures
- Path finding
- Clustering
