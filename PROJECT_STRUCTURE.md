# ImageGraph Project Structure

```
cursor_kg/
├── README.md                    # Main documentation
├── SETUP.md                     # Quick setup guide
├── ARCHITECTURE.md              # System architecture details
├── .gitignore                   # Git ignore rules
│
├── backend/                     # FastAPI Backend
│   ├── __init__.py
│   ├── main.py                  # FastAPI application entry point
│   ├── config.py                # Configuration manager
│   ├── database.py              # SQLite database layer
│   ├── requirements.txt         # Python dependencies
│   ├── pytest.ini               # Pytest configuration
│   │
│   ├── config/
│   │   └── config.yaml          # Application configuration
│   │
│   ├── services/                # Core services
│   │   ├── __init__.py
│   │   ├── scanner.py           # Folder/image scanning
│   │   ├── processor.py         # Image processing orchestrator
│   │   ├── graph_builder.py     # Knowledge graph construction
│   │   ├── graph_exporter.py    # Graph export (JSON/GraphML/Cypher)
│   │   │
│   │   └── analyzers/           # Image analysis modules
│   │       ├── __init__.py
│   │       ├── base.py          # Base analyzer interface
│   │       ├── caption_analyzer.py    # BLIP captioning
│   │       ├── ocr_analyzer.py         # Tesseract/EasyOCR
│   │       ├── embedding_analyzer.py    # CLIP embeddings
│   │       └── llm_analyzer.py         # Optional LLM enhancement
│   │
│   ├── tests/                   # Unit tests
│   │   ├── __init__.py
│   │   ├── test_database.py
│   │   └── test_graph_builder.py
│   │
│   └── data/                    # Runtime data (created on first run)
│       ├── imagegraph.db        # SQLite database
│       ├── faiss_index          # Vector index (if using FAISS)
│       └── thumbnails/          # Generated thumbnails
│
└── frontend/                    # React + Vite Frontend
    ├── package.json             # Node.js dependencies
    ├── vite.config.js           # Vite configuration
    ├── index.html               # HTML entry point
    │
    └── src/
        ├── main.jsx             # React entry point
        ├── App.jsx              # Main application component
        ├── App.css              # Main styles
        ├── index.css            # Global styles
        │
        └── components/          # React components
            ├── __init__.js
            ├── FolderSelector.jsx      # Folder selection UI
            ├── FolderSelector.css
            ├── GraphView.jsx           # Cytoscape.js graph visualization
            ├── GraphView.css
            ├── Filters.jsx             # Filter controls
            ├── Filters.css
            ├── ProgressBar.jsx         # Processing progress
            ├── ProgressBar.css
            ├── ImageDetail.jsx         # Image detail side panel
            └── ImageDetail.css
```

## Key Files Explained

### Backend

- **main.py**: FastAPI server with all API endpoints
- **database.py**: SQLite operations, schema, queries
- **processor.py**: Orchestrates all analyzers, processes images
- **graph_builder.py**: Core graph construction logic
- **analyzers/**: Modular image analysis (caption, OCR, embeddings, LLM)

### Frontend

- **App.jsx**: Main app state, routing, API calls
- **GraphView.jsx**: Cytoscape.js graph rendering
- **components/**: Reusable UI components

## Data Flow

1. User selects folder → `POST /api/scan`
2. Backend scans folder → `ImageScanner`
3. Background processing → `ImageProcessor` → Analyzers
4. Results saved → `Database`
5. Graph built → `GraphBuilder`
6. Frontend requests → `GET /api/graph`
7. Visualization → `GraphView` (Cytoscape.js)

## Configuration

- **backend/config/config.yaml**: All settings (thresholds, analyzers, storage)
- Environment variables: `LLM_API_KEY` for optional LLM mode

## Testing

- **backend/tests/**: Unit tests using pytest
- Run with: `pytest` from backend directory
