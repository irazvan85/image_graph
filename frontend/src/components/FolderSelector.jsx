import React, { useState } from 'react'
import './FolderSelector.css'

function FolderSelector({ onSelect }) {
  const [folderPath, setFolderPath] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (folderPath.trim()) {
      onSelect(folderPath.trim())
    }
  }

  return (
    <div className="folder-selector">
      <div className="folder-selector-card">
        <h2>Select Image Folder</h2>
        <p className="subtitle">Choose a folder containing images to analyze and build a knowledge graph</p>
        
        <form onSubmit={handleSubmit} className="folder-form">
          <div className="input-group">
            <label htmlFor="folder-path">Folder Path:</label>
            <input
              id="folder-path"
              type="text"
              value={folderPath}
              onChange={(e) => setFolderPath(e.target.value)}
              placeholder="C:\Users\YourName\Pictures or /home/user/images"
              className="folder-input"
            />
          </div>
          
          <button type="submit" className="btn-primary">
            Start Analysis
          </button>
        </form>

        <div className="info-box">
          <h3>Supported Formats</h3>
          <p>JPG, JPEG, PNG, WEBP, BMP, GIF</p>
          
          <h3>What happens next?</h3>
          <ul>
            <li>Images are analyzed for content, tags, and text</li>
            <li>A knowledge graph is built connecting images and concepts</li>
            <li>You can explore, filter, and export the graph</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

export default FolderSelector
