import React, { useState, useEffect } from 'react'
import './AnalyzerStatus.css'

function AnalyzerStatus() {
  const [config, setConfig] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const response = await fetch('/api/config')
        if (response.ok) {
          const data = await response.json()
          setConfig(data)
        }
      } catch (error) {
        console.error('Error fetching config:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchConfig()
  }, [])

  if (loading) {
    return <div className="analyzer-status">Loading...</div>
  }

  if (!config) {
    return <div className="analyzer-status">Unable to load configuration</div>
  }

  const getStatusIcon = (enabled) => {
    return enabled ? '✓' : '✗'
  }

  const getStatusClass = (enabled) => {
    return enabled ? 'status-enabled' : 'status-disabled'
  }

  return (
    <div className="analyzer-status">
      <h3 className="analyzer-status-title">Analyzer Status</h3>
      
      <div className="analyzer-list">
        <div className="analyzer-item">
          <span className={`status-indicator ${getStatusClass(config.analyzers.ocr?.enabled)}`}>
            {getStatusIcon(config.analyzers.ocr?.enabled)}
          </span>
          <span className="analyzer-name">OCR</span>
          {config.analyzers.ocr?.enabled && (
            <span className="analyzer-detail">({config.analyzers.ocr.engine})</span>
          )}
        </div>

        <div className="analyzer-item">
          <span className={`status-indicator ${getStatusClass(config.analyzers.captioning?.enabled)}`}>
            {getStatusIcon(config.analyzers.captioning?.enabled)}
          </span>
          <span className="analyzer-name">Captioning</span>
          {config.analyzers.captioning?.enabled && (
            <span className="analyzer-detail">({config.analyzers.captioning.model})</span>
          )}
        </div>

        <div className="analyzer-item">
          <span className={`status-indicator ${getStatusClass(config.analyzers.embeddings?.enabled)}`}>
            {getStatusIcon(config.analyzers.embeddings?.enabled)}
          </span>
          <span className="analyzer-name">Embeddings</span>
          {config.analyzers.embeddings?.enabled && (
            <span className="analyzer-detail">({config.analyzers.embeddings.model})</span>
          )}
        </div>

        {config.analyzers.object_detection?.enabled && (
          <div className="analyzer-item">
            <span className={`status-indicator ${getStatusClass(config.analyzers.object_detection?.enabled)}`}>
              {getStatusIcon(config.analyzers.object_detection?.enabled)}
            </span>
            <span className="analyzer-name">Object Detection</span>
            {config.analyzers.object_detection?.enabled && (
              <span className="analyzer-detail">({config.analyzers.object_detection.model})</span>
            )}
          </div>
        )}

        {config.analyzers.face_detection?.enabled && (
          <div className="analyzer-item">
            <span className={`status-indicator ${getStatusClass(config.analyzers.face_detection?.enabled)}`}>
              {getStatusIcon(config.analyzers.face_detection?.enabled)}
            </span>
            <span className="analyzer-name">Face Detection</span>
          </div>
        )}
      </div>

      <div className="llm-section">
        <div className={`llm-status ${config.llm?.active ? 'llm-active' : 'llm-inactive'}`}>
          <div className="llm-header">
            <span className={`status-indicator ${getStatusClass(config.llm?.active)}`}>
              {getStatusIcon(config.llm?.active)}
            </span>
            <span className="llm-label">LLM Mode</span>
          </div>
          {config.llm?.enabled && (
            <div className="llm-details">
              <div className="llm-detail-row">
                <span className="llm-detail-label">Model:</span>
                <span className="llm-detail-value">{config.llm.model}</span>
              </div>
              <div className="llm-detail-row">
                <span className="llm-detail-label">Provider:</span>
                <span className="llm-detail-value">{config.llm.provider}</span>
              </div>
              {!config.llm.active && config.llm.enabled && (
                <div className="llm-warning">
                  {!config.llm.has_api_key 
                    ? "API key not configured" 
                    : "LLM not active"}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default AnalyzerStatus
