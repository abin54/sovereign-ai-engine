import React, { useState } from 'react';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <div className="app-container">
      {/* Sidebar */}
      <nav className="sidebar glass-panel">
        <div className="logo">
          <div className="logo-icon">S</div>
          <span>SOVEREIGN</span>
        </div>
        <ul className="nav-links">
          <li className={activeTab === 'dashboard' ? 'active' : ''} onClick={() => setActiveTab('dashboard')}>
            Dashboard
          </li>
          <li className={activeTab === 'graphs' ? 'active' : ''} onClick={() => setActiveTab('graphs')}>
            Task Graphs
          </li>
          <li className={activeTab === 'audit' ? 'active' : ''} onClick={() => setActiveTab('audit')}>
            Audit Ledger
          </li>
          <li className={activeTab === 'settings' ? 'active' : ''} onClick={() => setActiveTab('settings')}>
            Settings
          </li>
        </ul>
      </nav>

      {/* Main Content */}
      <main className="content">
        <header className="header animate-in">
          <h1>{activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}</h1>
          <div className="status-badge">
            <span className="pulse"></span>
            System Operational
          </div>
        </header>

        {activeTab === 'dashboard' && (
          <div className="dashboard-grid animate-in">
            <div className="stat-card glass-panel">
              <h3>Active Tasks</h3>
              <div className="stat-value">12</div>
            </div>
            <div className="stat-card glass-panel">
              <h3>Policy Violations</h3>
              <div className="stat-value text-error">0</div>
            </div>
            <div className="stat-card glass-panel">
              <h3>Verified Logs</h3>
              <div className="stat-value text-success">1,284</div>
            </div>
            
            <div className="main-chart glass-panel">
              <h3>Execution Timeline</h3>
              <div className="chart-placeholder">
                <div className="bar h-60"></div>
                <div className="bar h-80"></div>
                <div className="bar h-40"></div>
                <div className="bar h-90"></div>
                <div className="bar h-50"></div>
              </div>
            </div>

            <div className="recent-activity glass-panel">
              <h3>Recent Audit Logs</h3>
              <div className="log-list">
                <div className="log-item">
                  <span className="log-time">12:45:10</span>
                  <span className="log-action">shell_command</span>
                  <span className="log-status success">SUCCESS</span>
                </div>
                <div className="log-item">
                  <span className="log-time">12:44:05</span>
                  <span className="log-action">read_file</span>
                  <span className="log-status success">SUCCESS</span>
                </div>
                <div className="log-item">
                  <span className="log-time">12:42:30</span>
                  <span className="log-action">shell_command</span>
                  <span className="log-status error">DENIED</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'graphs' && (
          <div className="graphs-view animate-in">
            <div className="glass-panel graph-canvas">
               <p className="placeholder-text">Task Graph Visualizer (React Flow)</p>
               <div className="node node-scan">scan_project</div>
               <div className="arrow arrow-1">→</div>
               <div className="node node-analyze">analyze_findings</div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
