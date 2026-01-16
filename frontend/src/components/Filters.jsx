import React from 'react'
import './Filters.css'

function Filters({ filters, onFiltersChange }) {
  const updateFilter = (key, value) => {
    onFiltersChange({
      ...filters,
      [key]: value
    })
  }

  return (
    <div className="filters">
      <h3>Filters</h3>
      
      <div className="filter-group">
        <label htmlFor="min-confidence">Min Confidence:</label>
        <input
          id="min-confidence"
          type="range"
          min="0"
          max="1"
          step="0.1"
          value={filters.min_confidence}
          onChange={(e) => updateFilter('min_confidence', parseFloat(e.target.value))}
        />
        <span className="filter-value">{filters.min_confidence.toFixed(1)}</span>
      </div>

      <div className="filter-group">
        <label htmlFor="min-similarity">Min Similarity:</label>
        <input
          id="min-similarity"
          type="range"
          min="0"
          max="1"
          step="0.1"
          value={filters.min_similarity}
          onChange={(e) => updateFilter('min_similarity', parseFloat(e.target.value))}
        />
        <span className="filter-value">{filters.min_similarity.toFixed(1)}</span>
      </div>

      <div className="filter-group">
        <label htmlFor="search">Search:</label>
        <input
          id="search"
          type="text"
          placeholder="Search concepts..."
          value={filters.search_query}
          onChange={(e) => updateFilter('search_query', e.target.value)}
          className="search-input"
        />
      </div>
    </div>
  )
}

export default Filters
