// import react hooks
import React, { useState } from 'react';
// import lucide icons
import { Play, Download, CheckCircle2, RefreshCw, AlertCircle } from 'lucide-react';
// import api client
import { api } from '../services/api';

export default function Navbar({ title, subtitle, onRefreshAll }) {
  // state etl running
  const [isRunning, setIsRunning] = useState(false);
  // state run message
  const [runMessage, setRunMessage] = useState(null);

  // trigger pipeline handler
  const handleQuickRun = async () => {
    setIsRunning(true); // set running true
    setRunMessage(null); // clear old message
    try {
      const res = await api.runEtl({}); // call etl api
      setRunMessage({ type: 'success', text: `Pipeline executed: ${res.valid_rows} clean, ${res.rejected_rows} rejected` }); // success text
      if (onRefreshAll) onRefreshAll(); // refresh parent pages
    } catch (err) {
      setRunMessage({ type: 'error', text: err.message || 'Pipeline execution failed' }); // error text
    } finally {
      setIsRunning(false); // set running false
    }
  };

  return (
    // top navigation bar
    <header className="topbar">
      <div>
        <h2 className="page-title">{title}</h2> {/* page header title */}
        <p className="page-subtitle">{subtitle}</p> {/* page description */}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {/* run feedback alert */}
        {runMessage && (
          <div
            className={`badge ${runMessage.type === 'success' ? 'badge-success' : 'badge-danger'}`}
            style={{ padding: '6px 12px' }}
          >
            {runMessage.type === 'success' ? <CheckCircle2 size={14} /> : <AlertCircle size={14} />}
            <span>{runMessage.text}</span>
          </div>
        )}

        {/* export clean button */}
        <a
          href={api.getCleanExportUrl('csv')} // clean csv link
          className="btn btn-secondary" // button secondary style
          download // trigger direct download
        >
          <Download size={15} /> {/* download file icon */}
          <span>Export Clean CSV</span> {/* button text */}
        </a>

        {/* quick run button */}
        <button
          className="btn btn-primary" // primary teal button
          onClick={handleQuickRun} // run handler click
          disabled={isRunning} // disable while running
        >
          {isRunning ? (
            <>
              <div className="spinner" style={{ width: '14px', height: '14px' }}></div> {/* loading spinner */}
              <span>Running ETL...</span> {/* running text */}
            </>
          ) : (
            <>
              <Play size={15} /> {/* play arrow icon */}
              <span>Execute Pipeline</span> {/* execute text */}
            </>
          )}
        </button>
      </div>
    </header>
  );
}
