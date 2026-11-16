// import react module
import React from 'react';
// import lucide icons
import {
  LayoutDashboard, // dashboard icon
  UploadCloud, // upload icon
  Activity, // monitor icon
  TableProperties, // table icon
  ShieldCheck, // audit icon
  Database, // database icon
  TrendingUp // pulse icon
} from 'lucide-react';

// define navigation items
const NAV_ITEMS = [
  { id: 'dashboard', label: 'Overview Dashboard', icon: LayoutDashboard }, // page 1
  { id: 'upload', label: 'Data Upload & Ingest', icon: UploadCloud }, // page 2
  { id: 'monitoring', label: 'ETL Pipeline Monitor', icon: Activity }, // page 3
  { id: 'explorer', label: 'Sales Explorer', icon: TableProperties }, // page 4
  { id: 'quality', label: 'Data Quality Audit', icon: ShieldCheck } // page 5
];

export default function Sidebar({ activeTab, setActiveTab }) {
  return (
    // sidebar container element
    <aside className="sidebar">
      {/* brand title section */}
      <div className="sidebar-brand">
        <div className="brand-icon-box">
          <TrendingUp size={20} /> {/* brand pulse icon */}
        </div>
        <div>
          <h1 className="brand-title">SalesPulse</h1> {/* app brand title */}
        </div>
        <span className="brand-badge">ETL v1.0</span> {/* version badge */}
      </div>

      {/* navigation items list */}
      <nav className="sidebar-nav">
        {NAV_ITEMS.map((item) => {
          const IconComponent = item.icon; // icon component
          const isActive = activeTab === item.id; // active tab match

          return (
            <button
              key={item.id} // react list key
              className={`nav-link ${isActive ? 'active' : ''}`} // conditional class
              onClick={() => setActiveTab(item.id)} // tab switch handler
            >
              <IconComponent size={18} /> {/* navigation item icon */}
              <span>{item.label}</span> {/* navigation label */}
            </button>
          );
        })}
      </nav>

      {/* sidebar bottom footer */}
      <div className="sidebar-footer">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
          <Database size={14} color="#10b981" /> {/* db status icon */}
          <span style={{ color: '#e2e8f0', fontWeight: 600 }}>PostgreSQL / SQLite</span> {/* database engine */}
        </div>
        <p style={{ fontSize: '0.75rem', color: '#64748b' }}>Connected & Synced</p> {/* connection note */}
      </div>
    </aside>
  );
}
