import React, { useState, useEffect } from 'react'
import './ImageDetail.css'

function ImageDetail({ imageId, onClose }) {
  const [metadata, setMetadata] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadMetadata()
  }, [imageId])

  const loadMetadata = async () => {
    setLoading(true)
    try {
      const response = await fetch(`/api/image/${imageId}`)
      const data = await response.json()
      setMetadata(data.metadata)
    } catch (error) {
      console.error('Error loading image metadata:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="image-detail">
        <div className="image-detail-header">
          <h3>Loading...</h3>
          <button onClick={onClose} className="close-btn">×</button>
        </div>
      </div>
    )
  }

  if (!metadata) {
    return (
      <div className="image-detail">
        <div className="image-detail-header">
          <h3>Image Not Found</h3>
          <button onClick={onClose} className="close-btn">×</button>
        </div>
      </div>
    )
  }

  return (
    <div className="image-detail">
      <div className="image-detail-header">
        <h3>Image Details</h3>
        <button onClick={onClose} className="close-btn">×</button>
      </div>
      
      <div className="image-detail-content">
        <div className="image-preview">
          <img 
            src={`/api/thumbnail/${imageId}`} 
            alt={metadata.file_path}
            onError={(e) => {
              e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200"><rect width="200" height="200" fill="%23ddd"/><text x="50%25" y="50%25" text-anchor="middle" dy=".3em" fill="%23999">No thumbnail</text></svg>'
            }}
          />
        </div>

        <div className="metadata-section">
          <h4>File Information</h4>
          <div className="metadata-item">
            <span className="label">Path:</span>
            <span className="value">{metadata.file_path}</span>
          </div>
          {metadata.width && metadata.height && (
            <div className="metadata-item">
              <span className="label">Dimensions:</span>
              <span className="value">{metadata.width} × {metadata.height}</span>
            </div>
          )}
          {metadata.file_size && (
            <div className="metadata-item">
              <span className="label">Size:</span>
              <span className="value">{(metadata.file_size / 1024).toFixed(2)} KB</span>
            </div>
          )}
        </div>

        {metadata.caption && (
          <div className="metadata-section">
            <h4>Caption</h4>
            <p>{metadata.caption}</p>
          </div>
        )}

        {metadata.tags && metadata.tags.length > 0 && (
          <div className="metadata-section">
            <h4>Tags</h4>
            <div className="tags-list">
              {metadata.tags.map((tag, idx) => (
                <span key={idx} className="tag">{tag}</span>
              ))}
            </div>
          </div>
        )}

        {metadata.ocr_text && (
          <div className="metadata-section">
            <h4>OCR Text</h4>
            <p className="ocr-text">{metadata.ocr_text}</p>
          </div>
        )}

        {metadata.ocr_entities && metadata.ocr_entities.length > 0 && (
          <div className="metadata-section">
            <h4>Extracted Entities</h4>
            <div className="entities-list">
              {metadata.ocr_entities.map((entity, idx) => (
                <div key={idx} className="entity-item">
                  <span className="entity-type">{entity.type}:</span>
                  <span className="entity-value">{entity.value}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default ImageDetail
