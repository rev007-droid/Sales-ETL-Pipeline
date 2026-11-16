// import react module
import React from 'react';
// import lucide icons
import { CheckCircle2, Clock, AlertTriangle, XCircle } from 'lucide-react';

export default function StatusBadge({ status }) {
  const norm = String(status || '').toUpperCase(); // normalize status string

  if (norm === 'COMPLETED' || norm === 'SUCCESS' || norm === 'PASSED') {
    return (
      <span className="badge badge-success">
        <CheckCircle2 size={12} /> {/* success check icon */}
        <span>{status}</span> {/* status label text */}
      </span>
    );
  }

  if (norm === 'PROCESSING' || norm === 'RUNNING') {
    return (
      <span className="badge badge-info">
        <Clock size={12} /> {/* processing clock icon */}
        <span>{status}</span> {/* status label text */}
      </span>
    );
  }

  if (norm === 'FAILED' || norm === 'ERROR') {
    return (
      <span className="badge badge-danger">
        <XCircle size={12} /> {/* danger cross icon */}
        <span>{status}</span> {/* status label text */}
      </span>
    );
  }

  // fallback warning badge
  return (
    <span className="badge badge-warning">
      <AlertTriangle size={12} /> {/* warning alert icon */}
      <span>{status || 'PENDING'}</span> {/* pending status label */}
    </span>
  );
}
