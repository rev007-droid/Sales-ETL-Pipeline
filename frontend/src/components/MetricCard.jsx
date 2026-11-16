// import react module
import React from 'react';

export default function MetricCard({ label, value, subtext, icon: Icon, trendColor = '#0d9488' }) {
  return (
    // metric card container
    <div className="metric-card">
      <div className="metric-label">
        <span>{label}</span> {/* metric name label */}
        {Icon && (
          <div style={{ color: trendColor }}>
            <Icon size={18} /> {/* custom metric icon */}
          </div>
        )}
      </div>
      <div className="metric-value">{value}</div> {/* formatted primary value */}
      {subtext && <div className="metric-footer">{subtext}</div>} {/* secondary context note */}
    </div>
  );
}
