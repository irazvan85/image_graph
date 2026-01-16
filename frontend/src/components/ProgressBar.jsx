import React from 'react'
import './ProgressBar.css'

function ProgressBar({ progress }) {
  const percentage = progress.total > 0 
    ? Math.round((progress.progress / progress.total) * 100)
    : 0

  return (
    <div className="progress-bar-container">
      <h3>Processing</h3>
      <div className="progress-info">
        <span>{progress.progress} / {progress.total}</span>
        <span>{percentage}%</span>
      </div>
      <div className="progress-bar">
        <div 
          className="progress-fill" 
          style={{ width: `${percentage}%` }}
        ></div>
      </div>
      {progress.current_file && (
        <div className="current-file">
          {progress.current_file.split(/[/\\]/).pop()}
        </div>
      )}
      {progress.status === 'error' && progress.error && (
        <div className="error-message">
          Error: {progress.error}
        </div>
      )}
    </div>
  )
}

export default ProgressBar
