import React, { useState } from 'react';
import LabInput from './components/LabInput';
import ResultsDisplay from './components/ResultsDisplay';
import { ActivitySquare, Loader2 } from 'lucide-react';
import './App.css';

function App() {
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleAnalyze = async (data) => {
    setIsLoading(true);
    setError(null);
    setResults([]);

    try {
      const response = await fetch('http://localhost:8000/analyze_labs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ results: data }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }

      const responseData = await response.json();
      setResults(responseData.analyzed_results);
    } catch (err) {
      console.error(err);
      setError('Failed to analyze lab results. Please ensure the backend is running and API keys are set.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="header-content">
          <ActivitySquare size={32} className="header-icon" />
          <h1>Clinical Lab Results Analyzer</h1>
        </div>
      </header>

      <main className="app-main">
        <div className="layout-grid">
          <div className="input-column">
            <h2 className="column-title">Data Input</h2>
            <LabInput onAnalyze={handleAnalyze} isLoading={isLoading} />
            
            {error && (
              <div className="error-banner">
                {error}
              </div>
            )}
            
            {isLoading && (
              <div className="loading-state">
                <Loader2 size={32} className="spinner" />
                <p>Analyzing results with AI...</p>
              </div>
            )}
          </div>
          
          <div className="results-column">
            <ResultsDisplay results={results} />
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
