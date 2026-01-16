# ImageGraph - Visual Knowledge Graph from Images

A production-ready application that generates an interactive knowledge graph from a folder of images by analyzing content, extracting entities/concepts, and connecting them in a visual graph.

## Features

- **Image Analysis**: Automatic content understanding with object/scene tags, OCR text extraction, and embeddings
- **Knowledge Graph**: Builds relationships between images and concepts with confidence scores
- **Interactive Visualization**: Zoom, pan, drag nodes, filter, and search
- **Incremental Updates**: Only processes new/changed files on re-scan
- **Export**: JSON, GraphML, and Neo4j/Cypher formats
- **Privacy-First**: All processing happens locally
- **LLM Mode**: Optional enhanced entity extraction using multimodal LLM APIs

## Architecture

```
ImageGraph/
├── backend/                    # FastAPI server
│   ├── services/               # Core services
│   │   ├── analyzers/          # Image analysis modules
│   │   ├── scanner.py          # Folder scanning
│   │   ├── processor.py        # Image processing orchestrator
│   │   ├── graph_builder.py    # Knowledge graph construction
│   │   └── graph_exporter.py   # Export functionality
│   ├── config/                 # Configuration files
│   ├── database.py             # SQLite database layer
│   ├── config.py               # Config management
│   ├── main.py                 # FastAPI application
│   └── tests/                  # Unit tests
├── frontend/                   # React + Vite app
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── App.jsx             # Main app component
│   │   └── main.jsx            # Entry point
│   └── package.json
└── README.md
```

### System Flow

1. **User selects folder** → Frontend sends POST /api/scan
2. **Backend scans folder** → Finds all images
3. **Background processing** → Each image is analyzed:
   - BLIP generates caption
   - Tesseract/EasyOCR extracts text
   - CLIP generates embeddings
   - Optional LLM enhances entities
4. **Graph building** → Creates nodes and edges:
   - Image nodes + Concept nodes
   - Image→Concept edges (from tags/OCR)
   - Concept→Concept edges (co-occurrence)
   - Image→Image edges (similarity)
5. **Visualization** → Cytoscape.js renders interactive graph

## Prerequisites

- Python 3.9+
- Node.js 18+
- Tesseract OCR (for Windows: download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki))
- CUDA-capable GPU (optional, for faster processing)

## Installation

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Tesseract OCR:
   - Windows: Download installer from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
   - Linux: `sudo apt-get install tesseract-ocr`
   - Mac: `brew install tesseract`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

## Configuration

Edit `backend/config/config.yaml` to customize:

- Similarity and confidence thresholds
- Enable/disable analyzers (OCR, captioning, detection)
- LLM API settings (optional)
- Processing batch sizes

## Running the Application

### Start Backend

1. Activate virtual environment (if not already active):
```bash
# Windows
cd backend
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

2. Start the FastAPI server:
```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

The backend will be available at http://localhost:8000

### Start Frontend

1. Open a new terminal window
2. Navigate to frontend directory:
```bash
cd frontend
```

3. Install dependencies (first time only):
```bash
npm install
```

4. Start the development server:
```bash
npm run dev
```

5. Open http://localhost:5173 in your browser.

## Usage

1. **Select Folder**: Click "Select Folder" and choose a directory containing images
2. **Scan**: The app will automatically start processing images in the background
3. **View Graph**: Explore the interactive graph visualization
4. **Filter & Search**: Use filters and search to find specific concepts or images
5. **Export**: Export the graph in your preferred format

## Performance

- Handles 5,000+ images efficiently with background processing
- Progress tracking and cancellation support
- Caching of analysis results
- Incremental updates for new/changed files

## Configuration

Edit `backend/config/config.yaml` to customize:

- **Processing thresholds**: Similarity, confidence, image similarity
- **Analyzers**: Enable/disable OCR, captioning, object detection
- **LLM Mode**: Optional enhanced entity extraction (requires API key)
- **Storage paths**: Database, vector index, thumbnails

### LLM Mode Setup (Optional)

To enable enhanced entity extraction with LLM:

1. Get an OpenAI API key from [platform.openai.com](https://platform.openai.com/)
2. Set environment variable:
   ```bash
   # Windows PowerShell
   $env:LLM_API_KEY="your-api-key-here"
   
   # Linux/Mac
   export LLM_API_KEY="your-api-key-here"
   ```
3. Enable in `config/config.yaml`:
   ```yaml
   llm:
     enabled: true
     provider: "openai"
     model: "gpt-4-vision-preview"
   ```

## Extending the Application

### Adding Neo4j Support

The graph structure is designed to be easily exportable to Neo4j. See `backend/services/graph_exporter.py` for Cypher export implementation. You can import the exported Cypher statements directly into Neo4j.

### Adding Custom Analyzers

1. Create a new analyzer class in `backend/services/analyzers/` extending `BaseAnalyzer`
2. Implement the `analyze(image_path)` method
3. Register in `backend/services/processor.py`

### Performance Tuning

- **Batch processing**: Adjust `batch_size` in config
- **Similarity thresholds**: Lower thresholds = more connections
- **Model selection**: Use smaller models (blip-base vs blip-large) for faster processing
- **GPU acceleration**: Install CUDA-enabled PyTorch for faster ML inference

## Troubleshooting

### Backend Issues

- **"Tesseract not found"**: Ensure Tesseract is installed and in PATH
- **"CUDA out of memory"**: Reduce batch_size or use CPU mode
- **Slow processing**: First run downloads models (~2GB). Subsequent runs are faster.

### Frontend Issues

- **"Cannot connect to backend"**: Ensure backend is running on port 8000
- **Graph not loading**: Check browser console for errors, verify API endpoints

## Testing

Run unit tests:
```bash
cd backend
pytest
```

## Export Formats

- **JSON**: Standard graph format with nodes and edges
- **GraphML**: XML format for graph visualization tools (Gephi, yEd)
- **Cypher**: Neo4j import format

## License

MIT

## License

MIT
