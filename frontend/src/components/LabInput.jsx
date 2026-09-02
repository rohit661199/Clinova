import React, { useState } from 'react';
import Papa from 'papaparse';
import { Upload, FileText, Send } from 'lucide-react';
import './LabInput.css';

const LabInput = ({ onAnalyze, isLoading }) => {
  const [activeTab, setActiveTab] = useState('csv');
  
  // Form State
  const [testName, setTestName] = useState('');
  const [result, setResult] = useState('');
  const [unit, setUnit] = useState('');
  const [refRange, setRefRange] = useState('');

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      Papa.parse(file, {
        header: true,
        skipEmptyLines: true,
        complete: function (results) {
          onAnalyze(results.data);
        }
      });
    }
  };

  const handleFormSubmit = (e) => {
    e.preventDefault();
    if (!testName || !result) return;
    
    // Attempt to parse refRange into min/max if possible
    let minRef = null;
    let maxRef = null;
    
    if (refRange && refRange.includes('-')) {
        const parts = refRange.split('-');
        if (parts.length === 2) {
            minRef = parseFloat(parts[0]);
            maxRef = parseFloat(parts[1]);
        }
    }

    const payload = [{
      Test_Name: testName,
      Result: result,
      Unit: unit,
      Reference_Range: refRange,
      Min_Reference: isNaN(minRef) ? null : minRef,
      Max_Reference: isNaN(maxRef) ? null : maxRef
    }];

    onAnalyze(payload);
  };

  return (
    <div className="lab-input-container">
      <div className="tabs">
        <button 
          className={`tab-button ${activeTab === 'csv' ? 'active' : ''}`}
          onClick={() => setActiveTab('csv')}
        >
          <Upload size={18} /> CSV Upload
        </button>
        <button 
          className={`tab-button ${activeTab === 'form' ? 'active' : ''}`}
          onClick={() => setActiveTab('form')}
        >
          <FileText size={18} /> Manual Entry
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'csv' ? (
          <div className="upload-section">
            <label className="upload-label">
              <Upload size={32} className="upload-icon" />
              <span>Click to upload a CSV file</span>
              <input type="file" accept=".csv" onChange={handleFileUpload} disabled={isLoading} hidden />
            </label>
            <p className="upload-hint">Expected columns: Test_Name, Result, Unit, Reference_Range (or Min_Reference, Max_Reference)</p>
          </div>
        ) : (
          <form className="manual-form" onSubmit={handleFormSubmit}>
            <div className="form-group">
              <label>Test Name *</label>
              <input type="text" value={testName} onChange={e => setTestName(e.target.value)} required disabled={isLoading} />
            </div>
            <div className="form-group row">
              <div className="form-col">
                <label>Result Value *</label>
                <input type="text" value={result} onChange={e => setResult(e.target.value)} required disabled={isLoading} />
              </div>
              <div className="form-col">
                <label>Unit</label>
                <input type="text" value={unit} onChange={e => setUnit(e.target.value)} disabled={isLoading} />
              </div>
            </div>
            <div className="form-group">
              <label>Reference Range (e.g. 10-20)</label>
              <input type="text" value={refRange} onChange={e => setRefRange(e.target.value)} disabled={isLoading} />
            </div>
            <button type="submit" className="submit-btn" disabled={isLoading || !testName || !result}>
               <Send size={18} /> Analyze
            </button>
          </form>
        )}
      </div>
    </div>
  );
};

export default LabInput;
