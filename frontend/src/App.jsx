import React, { useState, useEffect, useCallback, useRef } from 'react'
import FolderSelector from './components/FolderSelector'
import GraphView from './components/GraphView'
import GraphView3D from './components/GraphView3D'
import ImageDetail from './components/ImageDetail'
import ProgressBar from './components/ProgressBar'
import Filters from './components/Filters'
import AnalyzerStatus from './components/AnalyzerStatus'
import { DEMO_GRAPH } from './demoData'
import './App.css'

function App() {
  const [selectedFolder, setSelectedFolder] = useState(null)
  const [isDemoMode, setIsDemoMode] = useState(false)
  const [graph, setGraph] = useState({ nodes: [], edges: [] })
  const [selectedImage, setSelectedImage] = useState(null)
  const [progress, setProgress] = useState(null)
  const [viewMode, setViewMode] = useState('3d') // '2d' or '3d'
  const [filters, setFilters] = useState({
    min_confidence: 0.3,
    min_similarity: 0.7,
    search_query: ''
  })
  const graphLoadedRef = useRef(false)

  const loadGraph = useCallback(async () => {
    try {
      const params = new URLSearchParams()
      if (filters.min_confidence !== undefined) {
        params.append('min_confidence', filters.min_confidence)
      }
      if (filters.min_similarity !== undefined) {
        params.append('min_similarity', filters.min_similarity)
      }
      if (filters.search_query) {
        params.append('search_query', filters.search_query)
      }
      if (filters.concept_types && filters.concept_types.length > 0) {
        params.append('concept_types', filters.concept_types.join(','))
      }
      
      const response = await fetch(`/api/graph?${params}`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      
      // Ensure data has expected structure
      if (!data || !Array.isArray(data.nodes) || !Array.isArray(data.edges)) {
        console.error('Invalid graph data structure:', data)
        setGraph({ nodes: [], edges: [] })
        return
      }
      
      setGraph(data)
      graphLoadedRef.current = true
    } catch (error) {
      console.error('Error loading graph:', error)
      // Set empty graph on error to prevent crashes
      setGraph({ nodes: [], edges: [] })
    }
  }, [filters])

  useEffect(() => {
    // Poll for progress only if folder is selected and not in demo mode
    if (!selectedFolder || isDemoMode) return

    let intervalId = null
    
    const pollProgress = async () => {
      try {
        const response = await fetch('/api/progress')
        const data = await response.json()
        setProgress(data)
        
        // If processing is complete, refresh graph once and stop polling
        if (data.status === 'completed' && !graphLoadedRef.current) {
          await loadGraph()
          if (intervalId) {
            clearInterval(intervalId)
            intervalId = null
          }
        } else if (data.status === 'error' || data.status === 'cancelled') {
          // Stop polling on error or cancellation
          if (intervalId) {
            clearInterval(intervalId)
            intervalId = null
          }
        }
      } catch (error) {
        console.error('Error fetching progress:', error)
      }
    }

    // Start polling
    intervalId = setInterval(pollProgress, 1000)
    
    // Initial poll
    pollProgress()

    return () => {
      if (intervalId) {
        clearInterval(intervalId)
      }
    }
  }, [selectedFolder, isDemoMode, loadGraph])

  useEffect(() => {
    // Load graph when filters change (but only if folder is selected and graph was already loaded once)
    if (selectedFolder && graphLoadedRef.current && !isDemoMode) {
      loadGraph()
    }
  }, [filters, selectedFolder, isDemoMode, loadGraph])

  const handleFolderSelect = async (folderPath) => {
    setSelectedFolder(folderPath)
    setIsDemoMode(false)
    setSelectedImage(null)
    setGraph({ nodes: [], edges: [] })
    graphLoadedRef.current = false
    
    try {
      const response = await fetch('/api/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ folder_path: folderPath })
      })
      
      if (!response.ok) {
        throw new Error('Failed to start scan')
      }

      const data = await response.json()
      if (data.status === 'demo') {
        // Demo deployment: load demo graph and switch to demo mode
        setIsDemoMode(true)
        setGraph(DEMO_GRAPH)
        graphLoadedRef.current = true
      }
    } catch (error) {
      console.error('Error starting scan:', error)
      alert('Failed to start scan. Make sure the backend is running.')
    }
  }

  const handleDemoSelect = () => {
    setSelectedFolder('Demo Mode')
    setIsDemoMode(true)
    setSelectedImage(null)
    setGraph(DEMO_GRAPH)
    graphLoadedRef.current = true
    setProgress(null)
  }

  const handleRescan = async () => {
    if (!selectedFolder || isDemoMode) return
    
    graphLoadedRef.current = false
    
    try {
      const response = await fetch('/api/rescan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ folder_path: selectedFolder })
      })
      
      if (!response.ok) {
        throw new Error('Failed to start rescan')
      }
    } catch (error) {
      console.error('Error starting rescan:', error)
    }
  }

  const handleNodeClick = useCallback((node) => {
    if (node.type === 'image') {
      setSelectedImage(node.id)
    }
  }, [])

  const handleExport = async (format) => {
    try {
      const response = await fetch(`/api/export?format=${format}`)
      const data = await response.json()
      
      const blob = format === 'json' 
        ? new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
        : new Blob([data[format] || data.graphml || data.cypher], { type: 'text/plain' })
      
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `imagegraph.${format === 'json' ? 'json' : format === 'graphml' ? 'graphml' : 'cypher'}`
      a.click()
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Error exporting:', error)
      alert('Failed to export graph')
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>ImageGraph</h1>
        {isDemoMode && (
          <div className="demo-banner">✨ Demo Mode — <a href="https://github.com/irazvan85/image_graph" target="_blank" rel="noopener noreferrer" aria-label="Run ImageGraph locally — GitHub repository setup instructions">run locally</a> for full functionality</div>
        )}
        <div className="header-actions">
          {selectedFolder && (
            <>
              <div className="view-toggle">
                <button 
                  onClick={() => setViewMode('2d')} 
                  className={`btn-toggle ${viewMode === '2d' ? 'active' : ''}`}
                >
                  2D
                </button>
                <button 
                  onClick={() => setViewMode('3d')} 
                  className={`btn-toggle ${viewMode === '3d' ? 'active' : ''}`}
                >
                  3D
                </button>
              </div>
              {!isDemoMode && (
                <button onClick={handleRescan} className="btn-secondary">
                  Rescan Folder
                </button>
              )}
              <button onClick={() => handleExport('json')} className="btn-secondary">
                Export JSON
              </button>
              <button onClick={() => handleExport('graphml')} className="btn-secondary">
                Export GraphML
              </button>
              <button onClick={() => handleExport('cypher')} className="btn-secondary">
                Export Cypher
              </button>
              <button onClick={() => { setSelectedFolder(null); setIsDemoMode(false); setGraph({ nodes: [], edges: [] }) }} className="btn-secondary">
                ← Back
              </button>
            </>
          )}
        </div>
      </header>

      <main className="app-main">
        {!selectedFolder ? (
          <FolderSelector onSelect={handleFolderSelect} onDemoSelect={handleDemoSelect} />
        ) : (
          <>
            <div className="sidebar">
              {!isDemoMode && <AnalyzerStatus />}
              <Filters filters={filters} onFiltersChange={setFilters} />
              {progress && progress.status !== 'idle' && (
                <ProgressBar progress={progress} />
              )}
            </div>
            
            <div className="graph-container">
              {viewMode === '3d' ? (
                <GraphView3D 
                  graph={graph} 
                  onNodeClick={handleNodeClick}
                />
              ) : (
                <GraphView 
                  graph={graph} 
                  onNodeClick={handleNodeClick}
                />
              )}
            </div>

            {selectedImage && (
              <ImageDetail 
                imageId={selectedImage} 
                onClose={() => setSelectedImage(null)} 
              />
            )}
          </>
        )}
      </main>
    </div>
  )
}

export default App
