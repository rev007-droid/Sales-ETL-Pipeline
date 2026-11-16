// import react hooks
import React, { useState, useEffect } from 'react';
// import lucide icons
import {
  Activity, // activity icon
  RefreshCw, // refresh icon
  AlertCircle, // alert icon
  Download, // download icon
  CheckCircle2, // success icon
  Clock, // clock icon
  ChevronRight // chevron icon
} from 'lucide-react';
// import api service
import { api } from '../services/api';
// import status badge
import StatusBadge from '../components/StatusBadge';
// import formatters
import { formatNumber, formatDate } from '../utils/formatters';

export default function MonitoringPage() {
  // state jobs list
  const [jobs, setJobs] = useState([]);
  // state selected job
  const [selectedJob, setSelectedJob] = useState(null);
  // state job rejections
  const [rejections, setRejections] = useState([]);
  // state loading
  const [isLoading, setIsLoading] = useState(true);
  // state error
  const [error, setError] = useState(null);

  // fetch jobs list
  const loadJobs = async () => {
    setIsLoading(true); // start loading
    setError(null); // clear error
    try {
      const data = await api.getEtlJobs(30); // fetch 30 jobs
      setJobs(data.jobs || []); // save jobs
      if (data.jobs && data.jobs.length > 0 && !selectedJob) {
        loadJobDetail(data.jobs[0].id); // select first job
      }
    } catch (err) {
      setError(err.message || 'Failed to load ETL jobs'); // set error
    } finally {
      setIsLoading(false); // finish loading
    }
  };

  // fetch job details & rejections
  const loadJobDetail = async (jobId) => {
    try {
      const detail = await api.getEtlJobDetail(jobId); // fetch job detail
      setSelectedJob(detail.job); // set selected job
      setRejections(detail.rejections || []); // set rejections list
    } catch (err) {
      console.error('Failed to load job details', err); // log error
    }
  };

  // load on mount
  useEffect(() => {
    loadJobs(); // invoke load
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* monitoring header bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#0f172a' }}>ETL Pipeline Execution History</h3>
          <p style={{ fontSize: '0.85rem', color: '#64748b' }}>Real-time logs of automated and manual data ingestion runs</p>
        </div>
        <button className="btn btn-secondary" onClick={loadJobs} disabled={isLoading}>
          <RefreshCw size={14} className={isLoading ? 'spinner' : ''} />
          <span>Refresh Runs</span>
        </button>
      </div>

      {/* error message banner */}
      {error && (
        <div className="card" style={{ backgroundColor: '#fef2f2', borderColor: '#fca5a5', color: '#991b1b' }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* jobs list table */}
      <div className="card">
        <div className="card-header">
          <div>
            <h4 className="card-title">Ingestion Job Runs</h4>
            <p className="card-description">Click a run to inspect its row-level audit trail and validation rejections</p>
          </div>
        </div>

        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Job Name</th>
                <th>File Name</th>
                <th>Status</th>
                <th>Total Rows</th>
                <th>Clean</th>
                <th>Rejected</th>
                <th>Duplicates</th>
                <th>Duration</th>
                <th>Executed At</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((j) => {
                const isSelected = selectedJob?.id === j.id;
                return (
                  <tr
                    key={j.id}
                    onClick={() => loadJobDetail(j.id)}
                    style={{ cursor: 'pointer', backgroundColor: isSelected ? '#f0fdfa' : undefined }}
                  >
                    <td style={{ fontWeight: 600, color: '#0f172a' }}>{j.job_name}</td>
                    <td>{j.file_name}</td>
                    <td><StatusBadge status={j.status} /></td>
                    <td>{formatNumber(j.total_rows)}</td>
                    <td style={{ color: '#10b981', fontWeight: 600 }}>{formatNumber(j.valid_rows)}</td>
                    <td style={{ color: j.rejected_rows > 0 ? '#ef4444' : '#64748b', fontWeight: 600 }}>
                      {formatNumber(j.rejected_rows)}
                    </td>
                    <td>{formatNumber(j.duplicate_rows)}</td>
                    <td>{j.duration_seconds}s</td>
                    <td>{formatDate(j.created_at)}</td>
                    <td>
                      <span style={{ color: '#0d9488', display: 'flex', alignItems: 'center', gap: '2px', fontSize: '0.8rem', fontWeight: 600 }}>
                        Inspect <ChevronRight size={14} />
                      </span>
                    </td>
                  </tr>
                );
              })}
              {jobs.length === 0 && !isLoading && (
                <tr>
                  <td colSpan={10} style={{ textAlign: 'center', padding: '32px', color: '#94a3b8' }}>
                    No ETL job runs recorded yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* selected job audit & rejections */}
      {selectedJob && (
        <div className="card">
          <div className="card-header">
            <div>
              <h4 className="card-title">Run Audit Details: {selectedJob.job_name}</h4>
              <p className="card-description">
                Quality Score: <strong>{selectedJob.quality_score_pct}%</strong> • Clean Records: <strong>{selectedJob.valid_rows}</strong> • Rejections: <strong>{selectedJob.rejected_rows}</strong>
              </p>
            </div>
            {rejections.length > 0 && (
              <a
                href={api.getRejectedExportUrl('csv', selectedJob.id)}
                className="btn btn-secondary"
                download
              >
                <Download size={14} />
                <span>Download Rejections CSV</span>
              </a>
            )}
          </div>

          <h5 style={{ fontSize: '0.85rem', fontWeight: 600, color: '#64748b', marginBottom: '12px' }}>
            ROW-LEVEL REJECTION AUDIT LOG ({rejections.length} REJECTED RECORDS)
          </h5>

          <div className="table-container" style={{ maxHeight: '350px' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Row #</th>
                  <th>Order ID</th>
                  <th>Product</th>
                  <th>Rejection Reason</th>
                  <th>Raw Payload</th>
                </tr>
              </thead>
              <tbody>
                {rejections.map((r) => (
                  <tr key={r.id}>
                    <td style={{ fontWeight: 700, color: '#64748b' }}>#{r.row_number}</td>
                    <td style={{ fontWeight: 600 }}>{r.order_id || '(missing)'}</td>
                    <td>{r.product || '(missing)'}</td>
                    <td>
                      <span className="badge badge-danger">{r.rejection_reason}</span>
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: '#64748b' }}>
                      {r.raw_data ? r.raw_data.slice(0, 80) + '...' : '-'}
                    </td>
                  </tr>
                ))}
                {rejections.length === 0 && (
                  <tr>
                    <td colSpan={5} style={{ textAlign: 'center', padding: '24px', color: '#10b981', fontWeight: 600 }}>
                      <CheckCircle2 size={18} style={{ display: 'inline', marginRight: '6px', verticalAlign: 'middle' }} />
                      Clean Run! No rows were rejected during this pipeline execution.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
