import React from 'react';
import SeverityBadge from './SeverityBadge';
import { FileSearch, ArrowRight, Activity } from 'lucide-react';
import './ResultsDisplay.css';

const ResultsDisplay = ({ results }) => {
  if (!results || results.length === 0) {
    return (
      <div className="empty-results">
        <FileSearch size={48} className="empty-icon" />
        <h3>No results to display</h3>
        <p>Upload a CSV file or enter lab values manually to see AI analysis.</p>
      </div>
    );
  }

  return (
    <div className="results-container">
      <h2 className="results-title">
        <Activity size={24} /> Analysis Results
      </h2>
      <div className="results-list">
        {results.map((res, index) => (
          <div key={index} className={`result-card border-${res.Severity.toLowerCase()}`}>
            <div className="result-header">
              <div className="result-title-group">
                <h3 className="result-name">{res.Test_Name}</h3>
                <div className="result-value">
                  {res.Result} <span className="result-unit">{res.Unit}</span>
                </div>
              </div>
              <SeverityBadge severity={res.Severity} />
            </div>
            
            <div className="result-details">
              <div className="detail-item">
                <span className="detail-label">Reference Range:</span>
                <span className="detail-value">{res.Reference_Range}</span>
              </div>
            </div>

            <div className="ai-analysis">
              <div className="explanation">
                <strong>AI Explanation:</strong>
                <p>{res.Explanation}</p>
              </div>
              <div className="next-steps">
                <strong><ArrowRight size={16} /> Suggested Next Steps:</strong>
                <p>{res.Suggested_Next_Steps}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ResultsDisplay;
