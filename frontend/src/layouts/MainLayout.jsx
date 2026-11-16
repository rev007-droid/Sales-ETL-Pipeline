// import react hooks
import React, { useState, useEffect } from 'react';
// import sidebar component
import Sidebar from '../components/Sidebar';
// import navbar component
import Navbar from '../components/Navbar';
// import page components
import DashboardPage from '../pages/DashboardPage';
import UploadPage from '../pages/UploadPage';
import MonitoringPage from '../pages/MonitoringPage';
import SalesExplorerPage from '../pages/SalesExplorerPage';
import DataQualityPage from '../pages/DataQualityPage';
// import auth helper
import { getStoredUser, api } from '../services/api';

// page metadata dictionary
const PAGE_CONFIG = {
  dashboard: {
    title: 'Executive Sales Dashboard', // page title
    subtitle: 'Real-time sales performance, revenue trends, and operational KPIs' // page subtitle
  },
  upload: {
    title: 'Data Ingestion & Staging', // page title
    subtitle: 'Upload sales datasets, validate schemas, and trigger automated ETL' // page subtitle
  },
  monitoring: {
    title: 'ETL Pipeline Monitoring', // page title
    subtitle: 'Track batch job execution status, throughput, and error logs' // page subtitle
  },
  explorer: {
    title: 'Sales Data Explorer', // page title
    subtitle: 'Search, filter, paginate, and export clean sales transactions' // page subtitle
  },
  quality: {
    title: 'Data Quality & Reconciliation', // page title
    subtitle: 'Auditable data health scores, rejection analysis, and balance checks' // page subtitle
  }
};

export default function MainLayout() {
  // state active page tab
  const [activeTab, setActiveTab] = useState('dashboard');
  // state current auth user
  const [currentUser, setCurrentUser] = useState(getStoredUser());
  // state refresh key
  const [refreshKey, setRefreshKey] = useState(0);

  // sync auth user on mount
  useEffect(() => {
    if (getStoredUser()) {
      api.getMe()
        .then((u) => setCurrentUser(u))
        .catch(() => setCurrentUser(null));
    }
  }, []);

  // handle pipeline completion
  const handleRefreshAll = () => {
    setRefreshKey((k) => k + 1); // increment refresh key
  };

  // active config details
  const currentConfig = PAGE_CONFIG[activeTab] || PAGE_CONFIG.dashboard;

  return (
    // app layout wrapper
    <div className="app-layout">
      {/* sidebar navigation */}
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* main content area */}
      <div className="main-area">
        {/* top navigation header */}
        <Navbar
          title={currentConfig.title} // active title
          subtitle={currentConfig.subtitle} // active subtitle
          currentUser={currentUser} // current user state
          setCurrentUser={setCurrentUser} // set user state
          onRefreshAll={handleRefreshAll} // refresh callback
        />

        {/* page canvas container */}
        <main className="content-canvas" key={refreshKey}>
          {activeTab === 'dashboard' && <DashboardPage />} {/* render dashboard */}
          {activeTab === 'upload' && <UploadPage currentUser={currentUser} onEtlCompleted={handleRefreshAll} />} {/* render upload */}
          {activeTab === 'monitoring' && <MonitoringPage />} {/* render monitoring */}
          {activeTab === 'explorer' && <SalesExplorerPage />} {/* render explorer */}
          {activeTab === 'quality' && <DataQualityPage />} {/* render quality */}
        </main>
      </div>
    </div>
  );
}
