// import react hooks
import React, { useState } from 'react';
// import lucide icons
import {
  UploadCloud, // upload icon
  FileText, // file icon
  CheckCircle2, // success icon
  AlertTriangle, // warning icon
  Play, // play icon
  ArrowRight, // next icon
  Table // table icon
} from 'lucide-react';
// import api service
import { api } from '../services/api';
// import formatters
import { formatBytes, formatNumber } from '../utils/formatters';

export default function UploadPage({ onEtlCompleted }) {
  // state selected file
  const [file, setFile] = useState(null);
  // state is uploading
  const [isUploading, setIsUploading] = useState(false);
  // state upload response
  const [uploadData, setUploadData] = useState(null);
  // state upload error
  const [uploadError, setUploadError] = useState(null);

  // state is executing etl
  const [isExecuting, setIsExecuting] = useState(false);
  // state etl result
  const [etlResult, setEtlResult] = useState(null);
  // state etl error
  const [etlError, setEtlError] = useState(null);

  // drag state
  const [isDragging, setIsDragging] = useState(false);

  // handle file drop
  const handleDrop = (e) => {
    e.preventDefault(); // prevent default
    setIsDragging(false); // reset drag
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelected(e.dataTransfer.files[0]); // select dropped file
    }
  };

  // select file handler
  const handleFileSelected = (selectedFile) => {
    setFile(selectedFile); // set file
    setUploadData(null); // clear old data
    setUploadError(null); // clear old error
    setEtlResult(null); // clear etl result
    setEtlError(null); // clear etl error
  };

  // upload file action
  const handleUpload = async () => {
    if (!file) return; // return if empty
    setIsUploading(true); // start upload
    setUploadError(null); // clear error
    try {
      const res = await api.uploadFile(file); // call api upload
      setUploadData(res); // save upload metadata
    } catch (err) {
      setUploadError(err.message || 'File upload failed'); // set error message
    } finally {
      setIsUploading(false); // finish upload
    }
  };

  // execute etl pipeline action
  const handleRunPipeline = async () => {
    if (!uploadData?.file_id) return; // return if no id
    setIsExecuting(true); // start etl
    setEtlError(null); // clear error
    try {
      const res = await api.runEtl({ file_id: uploadData.file_id }); // call etl api
      setEtlResult(res); // save etl result
      if (onEtlCompleted) onEtlCompleted(); // trigger refresh callback
    } catch (err) {
      setEtlError(err.message || 'ETL execution failed'); // set error message
    } finally {
      setIsExecuting(false); // finish etl
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* upload card container */}
      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">Upload Sales Dataset</h3> {/* upload title */}
            <p className="card-description">Select a CSV or Excel spreadsheet containing sales orders</p> {/* upload subtext */}
          </div>
        </div>

        {/* dropzone area */}
        <div
          className={`dropzone ${isDragging ? 'active' : ''}`} // conditional active
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }} // drag over
          onDragLeave={() => setIsDragging(false)} // drag leave
          onDrop={handleDrop} // file drop
          onClick={() => document.getElementById('file-upload-input').click()} // click trigger
        >
          <input
            id="file-upload-input" // input identifier
            type="file" // file input
            accept=".csv,.xlsx,.xls" // allowed types
            style={{ display: 'none' }} // hidden element
            onChange={(e) => e.target.files[0] && handleFileSelected(e.target.files[0])} // change handler
          />
          <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: '#ccfbf1', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#0d9488' }}>
            <UploadCloud size={24} /> {/* upload cloud icon */}
          </div>
          <div>
            <h4 style={{ fontSize: '1rem', fontWeight: 600, color: '#0f172a' }}>
              {file ? file.name : 'Click to upload or drag & drop'} {/* file title */}
            </h4>
            <p style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '4px' }}>
              Supported formats: CSV, XLSX, XLS (Maximum 50MB) {/* formats note */}
            </p>
          </div>
          {file && (
            <span className="badge badge-info">
              {formatBytes(file.size)} {/* formatted file size */}
            </span>
          )}
        </div>

        {/* upload error message */}
        {uploadError && (
          <div style={{ marginTop: '16px', padding: '12px', background: '#fef2f2', border: '1px solid #fca5a5', borderRadius: '6px', color: '#991b1b', fontSize: '0.85rem' }}>
            <strong>Upload Error:</strong> {uploadError}
          </div>
        )}

        {/* upload trigger button */}
        {file && !uploadData && (
          <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'flex-end' }}>
            <button
              className="btn btn-primary" // primary style
              onClick={handleUpload} // upload click
              disabled={isUploading} // disable uploading
            >
              {isUploading ? (
                <>
                  <div className="spinner" style={{ width: '14px', height: '14px' }}></div> {/* spinner */}
                  <span>Uploading & Validating...</span> {/* uploading state */}
                </>
              ) : (
                <>
                  <ArrowRight size={16} /> {/* right arrow */}
                  <span>Upload & Inspect Schema</span> {/* button label */}
                </>
              )}
            </button>
          </div>
        )}
      </div>

      {/* file inspection & metadata */}
      {uploadData && (
        <div className="card">
          <div className="card-header">
            <div>
              <h3 className="card-title">File Metadata & Preliminary Validation</h3> {/* metadata title */}
              <p className="card-description">Dataset verified and safely staged for ETL processing</p> {/* metadata subtext */}
            </div>
            <span className="badge badge-success">
              <CheckCircle2 size={12} /> {/* checkmark icon */}
              <span>Schema Valid</span> {/* valid badge */}
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '20px' }}>
            <div style={{ padding: '12px', background: '#f8fafc', borderRadius: '6px' }}>
              <span style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>FILE NAME</span>
              <p style={{ fontWeight: 600, color: '#0f172a', marginTop: '2px' }}>{uploadData.filename}</p>
            </div>
            <div style={{ padding: '12px', background: '#f8fafc', borderRadius: '6px' }}>
              <span style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>SIZE</span>
              <p style={{ fontWeight: 600, color: '#0f172a', marginTop: '2px' }}>{formatBytes(uploadData.file_size_bytes)}</p>
            </div>
            <div style={{ padding: '12px', background: '#f8fafc', borderRadius: '6px' }}>
              <span style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>DETECTED ROWS</span>
              <p style={{ fontWeight: 600, color: '#0f172a', marginTop: '2px' }}>{formatNumber(uploadData.total_rows)}</p>
            </div>
            <div style={{ padding: '12px', background: '#f8fafc', borderRadius: '6px' }}>
              <span style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>COLUMNS</span>
              <p style={{ fontWeight: 600, color: '#0f172a', marginTop: '2px' }}>{uploadData.columns.length} columns</p>
            </div>
          </div>

          {/* preview table */}
          <h4 style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Table size={16} /> {/* table icon */}
            <span>Source Data Preview (First 10 Rows)</span> {/* preview label */}
          </h4>
          <div className="table-container" style={{ maxHeight: '300px' }}>
            <table className="data-table">
              <thead>
                <tr>
                  {uploadData.columns.map((col, idx) => (
                    <th key={idx}>{col}</th> // column headers
                  ))}
                </tr>
              </thead>
              <tbody>
                {uploadData.preview_rows.map((row, rIdx) => (
                  <tr key={rIdx}>
                    {uploadData.columns.map((col, cIdx) => (
                      <td key={cIdx}>{String(row[col] !== undefined && row[col] !== null ? row[col] : '')}</td> // cell value
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* etl execution button */}
          <div style={{ marginTop: '24px', display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
            <button
              className="btn btn-primary" // primary teal
              onClick={handleRunPipeline} // run handler
              disabled={isExecuting} // disable running
            >
              {isExecuting ? (
                <>
                  <div className="spinner" style={{ width: '14px', height: '14px' }}></div> {/* loading spinner */}
                  <span>Executing Pipeline...</span> {/* executing state */}
                </>
              ) : (
                <>
                  <Play size={16} /> {/* play icon */}
                  <span>Execute ETL Pipeline on this File</span> {/* execute text */}
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* etl execution feedback */}
      {etlError && (
        <div className="card" style={{ backgroundColor: '#fef2f2', borderColor: '#fca5a5', color: '#991b1b' }}>
          <strong>ETL Execution Error:</strong> {etlError}
        </div>
      )}

      {etlResult && (
        <div className="card" style={{ borderColor: '#10b981', backgroundColor: '#ecfdf5' }}>
          <div className="card-header">
            <div>
              <h3 className="card-title" style={{ color: '#065f46' }}>ETL Pipeline Execution Complete</h3>
              <p className="card-description" style={{ color: '#047857' }}>{etlResult.message}</p>
            </div>
            <span className="badge badge-success">
              <CheckCircle2 size={12} />
              <span>PASSED</span>
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '16px' }}>
            <div style={{ padding: '12px', background: '#fff', borderRadius: '6px', border: '1px solid #d1fae5' }}>
              <span style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>EXTRACTED ROWS</span>
              <p style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0f172a' }}>{formatNumber(etlResult.total_extracted)}</p>
            </div>
            <div style={{ padding: '12px', background: '#fff', borderRadius: '6px', border: '1px solid #d1fae5' }}>
              <span style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>CLEAN ROWS</span>
              <p style={{ fontSize: '1.25rem', fontWeight: 700, color: '#10b981' }}>{formatNumber(etlResult.valid_rows)}</p>
            </div>
            <div style={{ padding: '12px', background: '#fff', borderRadius: '6px', border: '1px solid #d1fae5' }}>
              <span style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>REJECTED ROWS</span>
              <p style={{ fontSize: '1.25rem', fontWeight: 700, color: '#ef4444' }}>{formatNumber(etlResult.rejected_rows)}</p>
            </div>
            <div style={{ padding: '12px', background: '#fff', borderRadius: '6px', border: '1px solid #d1fae5' }}>
              <span style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>QUALITY SCORE</span>
              <p style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0d9488' }}>{etlResult.quality_score_pct}%</p>
            </div>
            <div style={{ padding: '12px', background: '#fff', borderRadius: '6px', border: '1px solid #d1fae5' }}>
              <span style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>EXECUTION TIME</span>
              <p style={{ fontSize: '1.25rem', fontWeight: 700, color: '#2563eb' }}>{etlResult.duration_seconds}s</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
