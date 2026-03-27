import React, { useRef, useCallback, useMemo, useEffect } from 'react'
import ForceGraph3D from 'react-force-graph-3d'
import SpriteText from 'three-spritetext'
import * as THREE from 'three'
import './GraphView3D.css'

// Depth scale factor: controls vertical spread in 3D space
const DEPTH_SCALE = 120

// Node colors matching the 2D view
const NODE_COLORS = {
  image: '#3498db',
  concept: '#e74c3c'
}

// Edge colors matching the 2D view
const EDGE_COLORS = {
  image_concept: '#95a5a6',
  concept_concept: '#e67e22',
  image_image: '#9b59b6'
}

function GraphView3D({ graph, onNodeClick }) {
  const fgRef = useRef(null)
  const containerRef = useRef(null)

  // Transform graph data for 3d-force-graph format
  const graphData = useMemo(() => {
    if (!graph || !graph.nodes || !graph.edges) {
      return { nodes: [], links: [] }
    }

    const validNodeIds = new Set(graph.nodes.map(n => n.id))

    const nodes = graph.nodes.map(node => ({
      id: node.id,
      label: node.label || node.id,
      type: node.type || 'unknown',
      depth: node.depth !== undefined ? node.depth : (node.type === 'image' ? 0 : 1),
      conceptType: node.concept_type,
      filePath: node.file_path,
      // Fix Z position based on depth (semantic layer)
      fz: (node.depth !== undefined ? node.depth : (node.type === 'image' ? 0 : 1)) * DEPTH_SCALE
    }))

    const links = graph.edges
      .filter(edge => edge.source && edge.target && validNodeIds.has(edge.source) && validNodeIds.has(edge.target))
      .map(edge => ({
        source: edge.source,
        target: edge.target,
        type: edge.type || 'unknown',
        weight: edge.weight || edge.similarity || 1,
        similarity: edge.similarity
      }))

    return { nodes, links }
  }, [graph])

  // Focus camera on the graph after data changes
  useEffect(() => {
    if (fgRef.current && graphData.nodes.length > 0) {
      // Scale timeout with graph size: larger graphs need more time to settle
      const settleTime = Math.min(500 + graphData.nodes.length * 100, 3000)
      const timer = setTimeout(() => {
        fgRef.current.zoomToFit(400, 50)
      }, settleTime)
      return () => clearTimeout(timer)
    }
  }, [graphData])

  // Custom node rendering with Three.js objects
  const nodeThreeObject = useCallback((node) => {
    if (node.type === 'image') {
      // Image nodes: blue rounded box with label
      const group = new THREE.Group()

      const geometry = new THREE.BoxGeometry(8, 8, 4)
      const material = new THREE.MeshLambertMaterial({
        color: NODE_COLORS.image,
        transparent: true,
        opacity: 0.9
      })
      const mesh = new THREE.Mesh(geometry, material)
      group.add(mesh)

      // Add text label below
      const sprite = new SpriteText(node.label)
      sprite.color = '#ffffff'
      sprite.textHeight = 3
      sprite.position.y = -8
      sprite.backgroundColor = 'rgba(44, 62, 80, 0.7)'
      sprite.padding = 1
      sprite.borderRadius = 2
      group.add(sprite)

      return group
    } else {
      // Concept nodes: red sphere with label
      const group = new THREE.Group()

      const radius = 4 + Math.max(0, (node.depth - 1)) * 4 // Larger for more connected concepts
      const geometry = new THREE.SphereGeometry(radius, 16, 16)
      const material = new THREE.MeshLambertMaterial({
        color: NODE_COLORS.concept,
        transparent: true,
        opacity: 0.85
      })
      const mesh = new THREE.Mesh(geometry, material)
      group.add(mesh)

      // Add text label
      const sprite = new SpriteText(node.label)
      sprite.color = '#ffffff'
      sprite.textHeight = 3.5
      sprite.position.y = -(radius + 4)
      sprite.backgroundColor = 'rgba(231, 76, 60, 0.7)'
      sprite.padding = 1
      sprite.borderRadius = 2
      group.add(sprite)

      return group
    }
  }, [])

  // Custom link rendering
  const linkColor = useCallback((link) => {
    return EDGE_COLORS[link.type] || '#cccccc'
  }, [])

  const linkWidth = useCallback((link) => {
    if (link.type === 'image_concept') {
      return 0.5 + (link.weight || 0) * 2
    } else if (link.type === 'concept_concept') {
      return 0.5 + Math.min((link.weight || 0) / 5, 1) * 2
    } else if (link.type === 'image_image') {
      return 1.5
    }
    return 1
  }, [])

  const handleNodeClick = useCallback((node) => {
    if (node && onNodeClick) {
      onNodeClick({
        id: node.id,
        type: node.type,
        label: node.label,
        file_path: node.filePath,
        concept_type: node.conceptType,
        depth: node.depth
      })
    }
  }, [onNodeClick])

  // Handle container resize
  const [dimensions, setDimensions] = React.useState({ width: 800, height: 600 })
  
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect()
        setDimensions({ width: rect.width, height: rect.height })
      }
    }

    updateDimensions()
    window.addEventListener('resize', updateDimensions)

    // Use ResizeObserver for container-specific resizing
    let observer
    if (containerRef.current && typeof ResizeObserver !== 'undefined') {
      observer = new ResizeObserver(updateDimensions)
      observer.observe(containerRef.current)
    }

    return () => {
      window.removeEventListener('resize', updateDimensions)
      if (observer) observer.disconnect()
    }
  }, [])

  return (
    <div className="graph-view-3d" ref={containerRef}>
      {graphData.nodes.length > 0 ? (
        <ForceGraph3D
          ref={fgRef}
          graphData={graphData}
          width={dimensions.width}
          height={dimensions.height}
          backgroundColor="#1a1a2e"
          nodeThreeObject={nodeThreeObject}
          nodeThreeObjectExtend={false}
          linkColor={linkColor}
          linkWidth={linkWidth}
          linkOpacity={0.6}
          linkDirectionalArrowLength={3}
          linkDirectionalArrowRelPos={1}
          onNodeClick={handleNodeClick}
          nodeLabel={node => `${node.label} (${node.type}, depth: ${node.depth})`}
          d3AlphaDecay={0.02}
          d3VelocityDecay={0.3}
          warmupTicks={100}
          cooldownTicks={200}
        />
      ) : (
        <div className="graph-empty-3d">
          <p>No graph data to display. Select a folder or load demo data.</p>
        </div>
      )}

      <div className="graph-legend-3d">
        <h4>3D Knowledge Graph</h4>
        <div className="legend-section">
          <div className="legend-subtitle">Nodes</div>
          <div className="legend-item-3d">
            <div className="legend-color-3d" style={{ backgroundColor: NODE_COLORS.image }}></div>
            <span>Images (bottom layer)</span>
          </div>
          <div className="legend-item-3d">
            <div className="legend-color-3d" style={{ backgroundColor: NODE_COLORS.concept, borderRadius: '50%' }}></div>
            <span>Concepts (upper layers)</span>
          </div>
        </div>
        <div className="legend-section">
          <div className="legend-subtitle">Edges</div>
          <div className="legend-item-3d">
            <div className="legend-line-3d" style={{ backgroundColor: EDGE_COLORS.image_concept }}></div>
            <span>Image → Concept</span>
          </div>
          <div className="legend-item-3d">
            <div className="legend-line-3d" style={{ backgroundColor: EDGE_COLORS.concept_concept }}></div>
            <span>Concept → Concept</span>
          </div>
          <div className="legend-item-3d">
            <div className="legend-line-3d" style={{ backgroundColor: EDGE_COLORS.image_image }}></div>
            <span>Image → Image</span>
          </div>
        </div>
        <div className="legend-section">
          <div className="legend-subtitle">Z-Axis (Depth)</div>
          <div className="depth-legend">
            <span className="depth-label">↑ Abstract (hub concepts)</span>
            <div className="depth-bar"></div>
            <span className="depth-label">↓ Concrete (images)</span>
          </div>
        </div>
        <div className="legend-controls">
          <span>🖱️ Drag to rotate • Scroll to zoom • Right-click to pan</span>
        </div>
      </div>
    </div>
  )
}

export default GraphView3D
