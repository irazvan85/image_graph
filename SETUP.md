# Quick Setup Guide

## Step-by-Step Installation

### 1. Install Prerequisites

**Python 3.9+**
- Download from https://www.python.org/downloads/
- During installation, check "Add Python to PATH"

**Node.js 18+**
- Download from https://nodejs.org/
- Includes npm

**Tesseract OCR**
- **Windows**: 
  1. Download from https://github.com/UB-Mannheim/tesseract/wiki
  2. Install to default location (C:\Program Files\Tesseract-OCR)
  3. Add to PATH or set environment variable:
     ```
     TESSDATA_PREFIX=C:\Program Files\Tesseract-OCR\tessdata
     ```
- **Linux**: `sudo apt-get install tesseract-ocr`
- **Mac**: `brew install tesseract`

### 2. Clone/Download Project

```bash
cd C:\WS\cursor_kg  # or your project directory
```

### 3. Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies (this will take 10-15 minutes)
pip install -r requirements.txt
```

**First-time setup notes:**
- Downloads ~2GB of ML models (BLIP, CLIP)
- Requires stable internet connection
- May take 10-15 minutes

### 4. Frontend Setup

Open a **new terminal window**:

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install
```

### 5. Create Data Directory

```bash
# From project root
mkdir -p backend/data
mkdir -p backend/data/thumbnails
```

### 6. Run the Application

**Terminal 1 - Backend:**
```bash
cd backend
venv\Scripts\activate  # if not already activated
python -m uvicorn main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### 7. Open Browser

Navigate to: http://localhost:5173

## Verification

1. Backend should show: `Uvicorn running on http://0.0.0.0:8000`
2. Frontend should show: `Local: http://localhost:5173`
3. Browser should show the ImageGraph interface

## Troubleshooting

### "Tesseract not found"
- Verify Tesseract is installed
- Check PATH includes Tesseract installation directory
- Restart terminal after installing Tesseract

### "Module not found" errors
- Ensure virtual environment is activated
- Re-run `pip install -r requirements.txt`

### "Port already in use"
- Backend: Change port in `uvicorn` command: `--port 8001`
- Frontend: Vite will automatically use next available port

### Slow first run
- Normal! Models are downloading and initializing
- Subsequent runs will be faster

## Next Steps

1. Select a folder with images
2. Wait for processing to complete
3. Explore the knowledge graph!
