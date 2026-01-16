import React, { useEffect, useRef } from 'react'
import cytoscape from 'cytoscape'
import coseBilkent from 'cytoscape-cose-bilkent'
import './GraphView.css'

// Register layout
cytoscape.use(coseBilkent)

function GraphView({ graph, onNodeClick }) {
  const containerRef = useRef(null)
  const cyRef = useRef(null)

  useEffect(() => {
    if (!containerRef.current) return
    if (cyRef.current) return // Don't reinitialize if already exists

    // Initialize Cytoscape
    const cy = cytoscape({
      container: containerRef.current,
      elements: [],
      style: [
        {
          selector: 'node[type="image"]',
          style: {
            'background-color': '#3498db',
            'label': 'data(label)',
            'width': 40,
            'height': 40,
            'shape': 'round-rectangle',
            'font-size': '12px',
            'text-valign': 'bottom',
            'text-halign': 'center',
            'text-margin-y': 5
          }
        },
        {
          selector: 'node[type="concept"]',
          style: {
            'background-color': '#e74c3c',
            'label': 'data(label)',
            'width': 30,
            'height': 30,
            'shape': 'ellipse',
            'font-size': '11px',
            'text-valign': 'center',
            'text-halign': 'center'
          }
        },
        {
          selector: 'edge[type="image_concept"]',
          style: {
            'width': 'mapData(weight, 0, 1, 1, 5)',
            'line-color': '#95a5a6',
            'target-arrow-color': '#95a5a6',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier'
          }
        },
        {
          selector: 'edge[type="concept_concept"]',
          style: {
            'width': 'mapData(weight, 0, 10, 1, 3)',
            'line-color': '#e67e22',
            'target-arrow-color': '#e67e22',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier'
          }
        },
        {
          selector: 'edge[type="image_image"]',
          style: {
            'width': 2,
            'line-color': '#9b59b6',
            'target-arrow-color': '#9b59b6',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'opacity': 'mapData(similarity, 0, 1, 0.3, 1)'
          }
        }
      ],
      layout: {
        name: 'cose-bilkent',
        idealEdgeLength: 100,
        nodeDimensionsIncludeLabels: true
      },
      minZoom: 0.1,
      maxZoom: 3
    })

    cyRef.current = cy

    // Handle node clicks
    cy.on('tap', 'node', (evt) => {
      const node = evt.target
      onNodeClick(node.data())
    })

    // Cleanup
    return () => {
      if (cyRef.current) {
        cyRef.current.destroy()
        cyRef.current = null
      }
    }
  }, [onNodeClick])

  // Update click handler when onNodeClick changes
  useEffect(() => {
    if (!cyRef.current) return
    
    // Remove old handler and add new one
    cyRef.current.off('tap', 'node')
    cyRef.current.on('tap', 'node', (evt) => {
      const node = evt.target
      onNodeClick(node.data())
    })
  }, [onNodeClick])

  useEffect(() => {
    if (!cyRef.current) return
    if (!graph || !graph.nodes || !graph.edges) return
    if (graph.nodes.length === 0 && graph.edges.length === 0) return

    try {
      // Create a set of valid node IDs to filter orphaned edges
      const validNodeIds = new Set(graph.nodes.map(node => node.id))
      
      // Update graph data
      const nodeElements = graph.nodes.map(node => ({
        data: {
          id: node.id,
          label: node.label || node.id,
          type: node.type || 'unknown',
          ...node
        },
        group: 'nodes'
      }))
      
      // Filter edges to only include those with valid source and target nodes
      const edgeElements = graph.edges
        .filter(edge => {
          if (!edge.source || !edge.target) return false
          return validNodeIds.has(edge.source) && validNodeIds.has(edge.target)
        })
        .map(edge => ({
          data: {
            id: edge.id || `${edge.source}_${edge.target}`,
            source: edge.source,
            target: edge.target,
            type: edge.type || 'unknown',
            weight: edge.weight || edge.similarity || 1,
            similarity: edge.similarity
          },
          group: 'edges'
        }))

      const elements = [...nodeElements, ...edgeElements]

      // Only update if we have elements
      if (elements.length > 0) {
        cyRef.current.elements().remove()
        cyRef.current.add(elements)
        cyRef.current.layout({ name: 'cose-bilkent', idealEdgeLength: 100 }).run()
      }
    } catch (error) {
      console.error('Error updating graph:', error)
    }
  }, [graph])

  return (
    <div className="graph-view">
      <div ref={containerRef} className="cytoscape-container" />
      <div className="graph-legend">
        <div className="legend-item">
          <div className="legend-color" style={{ backgroundColor: '#3498db' }}></div>
          <span>Images</span>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{ backgroundColor: '#e74c3c' }}></div>
          <span>Concepts</span>
        </div>
        <div className="legend-item">
          <div className="legend-line" style={{ borderColor: '#95a5a6' }}></div>
          <span>Image-Concept</span>
        </div>
        <div className="legend-item">
          <div className="legend-line" style={{ borderColor: '#e67e22' }}></div>
          <span>Concept-Concept</span>
        </div>
        <div className="legend-item">
          <div className="legend-line" style={{ borderColor: '#9b59b6' }}></div>
          <span>Image-Image</span>
        </div>
      </div>
    </div>
  )
}

export default GraphView
