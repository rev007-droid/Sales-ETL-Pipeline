// import react hooks
import React, { useState } from 'react';
// import lucide icons
import { Play, Download, CheckCircle2, AlertCircle, User, LogOut, LogIn, Shield } from 'lucide-react';
// import api client
import { api } from '../services/api';
// import auth modal
import AuthModal from './AuthModal';

export default function Navbar({ title, subtitle, currentUser, setCurrentUser, onRefreshAll }) {
  // state etl running
  const [isRunning, setIsRunning] = useState(false);
  // state run message
  const [runMessage, setRunMessage] = useState(null);
  // state auth modal open
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);

  // trigger pipeline handler
  const handleQuickRun = async () => {
    // check viewer role guard
    if (currentUser && currentUser.role?.toLowerCase() === 'viewer') {
      setRunMessage({ type: 'error', text: "Access Denied: Viewers cannot execute ETL pipelines. Please switch to an 'Analyst' or 'Admin' role." });
      return;
    }

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

  // handle user logout
  const handleLogout = async () => {
    await api.logout();
    setCurrentUser(null);
    if (onRefreshAll) onRefreshAll();
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
          <span>Export Clean</span> {/* button text */}
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

        {/* auth user profile or login */}
        {currentUser ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', paddingLeft: '12px', borderLeft: '1px solid var(--border-light)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{ width: '32px', height: '32px', borderRadius: '50%', backgroundColor: '#0d9488', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: '0.85rem' }}>
                {(currentUser.full_name || currentUser.username || 'U')[0].toUpperCase()}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#0f172a', lineHeight: 1.2 }}>
                  {currentUser.full_name || currentUser.username}
                </span>
                <span className={`badge ${currentUser.role === 'admin' ? 'badge-warning' : currentUser.role === 'analyst' ? 'badge-info' : 'badge-secondary'}`} style={{ padding: '1px 6px', fontSize: '0.65rem', alignSelf: 'flex-start', marginTop: '2px' }}>
                  {currentUser.role?.toUpperCase()}
                </span>
              </div>
            </div>

            <button
              onClick={handleLogout}
              className="btn btn-secondary"
              style={{ padding: '6px 10px', fontSize: '0.8rem' }}
              title="Sign Out"
            >
              <LogOut size={14} />
            </button>
          </div>
        ) : (
          <div style={{ paddingLeft: '12px', borderLeft: '1px solid var(--border-light)' }}>
            <button
              onClick={() => setIsAuthModalOpen(true)}
              className="btn btn-secondary"
              style={{ padding: '8px 14px' }}
            >
              <LogIn size={15} />
              <span>Sign In</span>
            </button>
          </div>
        )}
      </div>

      {/* auth modal dialog */}
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        onAuthSuccess={(user) => {
          setCurrentUser(user);
          if (onRefreshAll) onRefreshAll();
        }}
      />
    </header>
  );
}
