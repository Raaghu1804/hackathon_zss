// frontend/src/App.jsx

import React, { useState, useEffect } from 'react';
import { Activity, Cpu, MessageSquare, BarChart3, AlertCircle, TrendingUp, Server, Gauge } from 'lucide-react';

// API Service
const API_BASE = 'http://localhost:8000';

const api = {
  getUnitsStatus: async () => {
    const response = await fetch(`${API_BASE}/api/units/status`);
    return response.json();
  },
  getAgentCommunications: async () => {
    const response = await fetch(`${API_BASE}/api/agents/communications`);
    return response.json();
  },
  queryAnalytics: async (question) => {
    const response = await fetch(`${API_BASE}/api/analytics/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question })
    });
    return response.json();
  },
  getHistoricalData: async (unit, hours = 24) => {
    const response = await fetch(`${API_BASE}/api/sensors/historical/${unit}?hours=${hours}`);
    return response.json();
  }
};

// Metric Card Component
const MetricCard = ({ title, value, unit, trend, status }) => {
  const statusColors = {
    normal: '#4caf50',
    warning: '#ff9800',
    critical: '#f44336'
  };

  return (
    <div className="metric-card">
      <div className="metric-header">
        <h3>{title}</h3>
        <span className={`status-badge status-${status}`}>
          <span className="status-dot" style={{ backgroundColor: statusColors[status] }}></span>
          {status}
        </span>
      </div>
      <div className="metric-value">
        <span className="value">{value}</span>
        <span className="unit">{unit}</span>
      </div>
      {trend && (
        <div className="metric-trend">
          <TrendingUp size={16} />
          <span>{trend}%</span>
        </div>
      )}
    </div>
  );
};

// Unit Status Card Component
const UnitStatusCard = ({ unit, data }) => {
  const getUnitIcon = (unitName) => {
    switch(unitName) {
      case 'precalciner': return <Server size={24} />;
      case 'rotary_kiln': return <Cpu size={24} />;
      case 'clinker_cooler': return <Activity size={24} />;
      default: return <Server size={24} />;
    }
  };

  const formatUnitName = (name) => {
    return name.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  return (
    <div className="unit-card">
      <div className="unit-header">
        <div className="unit-title">
          {getUnitIcon(unit)}
          <h2>{formatUnitName(unit)}</h2>
        </div>
        <span className={`status-indicator status-${data?.status || 'normal'}`}>
          {data?.status || 'normal'}
        </span>
      </div>
      
      <div className="unit-metrics">
        <div className="metric-row">
          <span className="metric-label">Health Score</span>
          <div className="metric-bar">
            <div 
              className="metric-bar-fill"
              style={{ 
                width: `${data?.overall_health || 0}%`,
                backgroundColor: data?.overall_health > 70 ? '#4caf50' : 
                               data?.overall_health > 40 ? '#ff9800' : '#f44336'
              }}
            />
          </div>
          <span className="metric-percentage">{data?.overall_health || 0}%</span>
        </div>
        
        <div className="metric-row">
          <span className="metric-label">Efficiency</span>
          <div className="metric-bar">
            <div 
              className="metric-bar-fill"
              style={{ 
                width: `${data?.efficiency || 0}%`,
                backgroundColor: '#00bcd4'
              }}
            />
          </div>
          <span className="metric-percentage">{data?.efficiency || 0}%</span>
        </div>
      </div>
      
      {data?.sensors && (
        <div className="sensor-grid">
          {data.sensors.slice(0, 4).map((sensor, idx) => (
            <div key={idx} className="sensor-item">
              <span className="sensor-name">{sensor.sensor_name.replace(/_/g, ' ')}</span>
              <span className={`sensor-value ${sensor.is_anomaly ? 'anomaly' : ''}`}>
                {sensor.value.toFixed(2)} {sensor.unit_measure}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Communication Item Component
const CommunicationItem = ({ comm }) => {
  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const severityColors = {
    info: '#2196f3',
    warning: '#ff9800',
    critical: '#f44336'
  };

  return (
    <div className="comm-item">
      <div className="comm-header">
        <div className="comm-agents">
          <span className="agent-from">{comm.from_agent}</span>
          <span className="arrow">→</span>
          <span className="agent-to">{comm.to_agent}</span>
        </div>
        <div className="comm-meta">
          <span 
            className="severity-badge"
            style={{ backgroundColor: severityColors[comm.severity] }}
          >
            {comm.severity}
          </span>
          <span className="timestamp">{formatTime(comm.timestamp)}</span>
        </div>
      </div>
      <div className="comm-message">{comm.message}</div>
      {comm.action_taken && (
        <div className="comm-action">
          <strong>Action:</strong> {comm.action_taken}
        </div>
      )}
    </div>
  );
};

// Main App Component
function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [unitsStatus, setUnitsStatus] = useState([]);
  const [communications, setCommunications] = useState([]);
  const [analyticsQuery, setAnalyticsQuery] = useState('');
  const [analyticsResponse, setAnalyticsResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);

  useEffect(() => {
    // Load initial data
    loadUnitsStatus();
    loadCommunications();
    
    // Setup WebSocket connection
    const ws = new WebSocket('ws://localhost:8000/ws');
    
    ws.onopen = () => {
      setWsConnected(true);
      console.log('WebSocket connected');
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'sensor_update') {
        // Update real-time data
        loadUnitsStatus();
      }
    };
    
    ws.onclose = () => {
      setWsConnected(false);
      console.log('WebSocket disconnected');
    };
    
    // Periodic refresh
    const interval = setInterval(() => {
      if (activeTab === 'dashboard') loadUnitsStatus();
      if (activeTab === 'communications') loadCommunications();
    }, 5000);
    
    return () => {
      ws.close();
      clearInterval(interval);
    };
  }, [activeTab]);

  const loadUnitsStatus = async () => {
    try {
      const data = await api.getUnitsStatus();
      setUnitsStatus(data);
    } catch (error) {
      console.error('Error loading units status:', error);
    }
  };

  const loadCommunications = async () => {
    try {
      const data = await api.getAgentCommunications();
      setCommunications(data);
    } catch (error) {
      console.error('Error loading communications:', error);
    }
  };

  const handleAnalyticsQuery = async () => {
    if (!analyticsQuery.trim()) return;
    
    setLoading(true);
    try {
      const response = await api.queryAnalytics(analyticsQuery);
      setAnalyticsResponse(response);
    } catch (error) {
      console.error('Error querying analytics:', error);
    }
    setLoading(false);
  };

  const renderDashboard = () => (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h1>Plant Operations Dashboard</h1>
        <div className="connection-status">
          <span className={`status-dot ${wsConnected ? 'connected' : 'disconnected'}`}></span>
          {wsConnected ? 'Real-time Connected' : 'Connecting...'}
        </div>
      </div>
      
      <div className="overview-cards">
        <MetricCard 
          title="Plant Efficiency" 
          value="87.5" 
          unit="%" 
          trend={2.3}
          status="normal"
        />
        <MetricCard 
          title="Energy Consumption" 
          value="142.8" 
          unit="MW" 
          trend={-1.2}
          status="normal"
        />
        <MetricCard 
          title="Production Rate" 
          value="285" 
          unit="t/h" 
          trend={0.8}
          status="warning"
        />
        <MetricCard 
          title="Active Alerts" 
          value="3" 
          unit="" 
          status="warning"
        />
      </div>
      
      <div className="units-grid">
        {unitsStatus.map((unit, idx) => (
          <UnitStatusCard key={idx} unit={unit.unit} data={unit} />
        ))}
      </div>
    </div>
  );

  const renderCommunications = () => (
    <div className="communications-container">
      <div className="comm-header">
        <h1>Agent Communications</h1>
        <div className="comm-stats">
          <span>Total: {communications.length}</span>
          <span className="critical-count">
            Critical: {communications.filter(c => c.severity === 'critical').length}
          </span>
        </div>
      </div>
      
      <div className="comm-list">
        {communications.length === 0 ? (
          <div className="empty-state">
            <MessageSquare size={48} />
            <p>No agent communications yet</p>
          </div>
        ) : (
          communications.map((comm, idx) => (
            <CommunicationItem key={idx} comm={comm} />
          ))
        )}
      </div>
    </div>
  );

  const renderAnalytics = () => (
    <div className="analytics-container">
      <div className="analytics-header">
        <h1>AI Analytics</h1>
        <p>Ask questions about plant operations and receive AI-powered insights</p>
      </div>
      
      <div className="query-section">
        <div className="query-input-wrapper">
          <input
            type="text"
            className="query-input"
            placeholder="Ask about plant operations, efficiency, or optimization..."
            value={analyticsQuery}
            onChange={(e) => setAnalyticsQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleAnalyticsQuery()}
          />
          <button 
            className="query-button"
            onClick={handleAnalyticsQuery}
            disabled={loading}
          >
            {loading ? 'Analyzing...' : 'Analyze'}
          </button>
        </div>
        
        <div className="query-suggestions">
          <span>Try asking:</span>
          <button 
            className="suggestion-chip"
            onClick={() => setAnalyticsQuery("What is the current efficiency of the pre-calciner?")}
          >
            Pre-calciner efficiency
          </button>
          <button 
            className="suggestion-chip"
            onClick={() => setAnalyticsQuery("How can we optimize the rotary kiln temperature?")}
          >
            Kiln optimization
          </button>
          <button 
            className="suggestion-chip"
            onClick={() => setAnalyticsQuery("What are the main issues in the clinker cooler?")}
          >
            Cooler issues
          </button>
        </div>
      </div>
      
      {analyticsResponse && (
        <div className="response-section">
          <div className="response-header">
            <div className="responding-agent">
              <Cpu size={20} />
              <span>{analyticsResponse.responding_agent}</span>
            </div>
            <div className="confidence">
              Confidence: {(analyticsResponse.confidence * 100).toFixed(0)}%
            </div>
          </div>
          <div className="response-content">
            {analyticsResponse.answer}
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div className="app">
      <nav className="navbar">
        <div className="nav-brand">
          <Gauge size={28} />
          <span>Cement AI Optimizer</span>
        </div>
        
        <div className="nav-tabs">
          <button 
            className={`nav-tab ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <Activity size={20} />
            Dashboard
          </button>
          <button 
            className={`nav-tab ${activeTab === 'communications' ? 'active' : ''}`}
            onClick={() => setActiveTab('communications')}
          >
            <MessageSquare size={20} />
            Communications
          </button>
          <button 
            className={`nav-tab ${activeTab === 'analytics' ? 'active' : ''}`}
            onClick={() => setActiveTab('analytics')}
          >
            <BarChart3 size={20} />
            AI Analytics
          </button>
        </div>
        
        <div className="nav-actions">
          <button className="nav-alert">
            <AlertCircle size={20} />
            <span className="alert-badge">3</span>
          </button>
        </div>
      </nav>
      
      <main className="main-content">
        {activeTab === 'dashboard' && renderDashboard()}
        {activeTab === 'communications' && renderCommunications()}
        {activeTab === 'analytics' && renderAnalytics()}
      </main>
      
      <style jsx>{`
        .app {
          min-height: 100vh;
          background: linear-gradient(135deg, #0a0e1a 0%, #141b2d 100%);
        }
        
        .navbar {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 1rem 2rem;
          background: rgba(26, 34, 53, 0.9);
          backdrop-filter: blur(10px);
          border-bottom: 1px solid #2a3553;
        }
        
        .nav-brand {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          font-size: 1.25rem;
          font-weight: 700;
          color: #00bcd4;
        }
        
        .nav-tabs {
          display: flex;
          gap: 0.5rem;
        }
        
        .nav-tab {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.75rem 1.5rem;
          background: transparent;
          border: none;
          color: #a8b2d1;
          cursor: pointer;
          border-radius: 8px;
          transition: all 0.3s ease;
          font-size: 0.95rem;
        }
        
        .nav-tab:hover {
          background: rgba(0, 188, 212, 0.1);
          color: #00bcd4;
        }
        
        .nav-tab.active {
          background: rgba(0, 188, 212, 0.15);
          color: #00bcd4;
          font-weight: 600;
        }
        
        .nav-actions {
          display: flex;
          gap: 1rem;
        }
        
        .nav-alert {
          position: relative;
          padding: 0.5rem;
          background: transparent;
          border: 1px solid #2a3553;
          border-radius: 8px;
          color: #a8b2d1;
          cursor: pointer;
        }
        
        .alert-badge {
          position: absolute;
          top: -4px;
          right: -4px;
          background: #f44336;
          color: white;
          font-size: 0.7rem;
          padding: 0.15rem 0.4rem;
          border-radius: 10px;
        }
        
        .main-content {
          padding: 2rem;
          max-width: 1600px;
          margin: 0 auto;
        }
        
        /* Dashboard Styles */
        .dashboard-container {
          display: flex;
          flex-direction: column;
          gap: 2rem;
        }
        
        .dashboard-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        
        .dashboard-header h1 {
          font-size: 2rem;
          font-weight: 600;
        }
        
        .connection-status {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.5rem 1rem;
          background: rgba(26, 34, 53, 0.7);
          border-radius: 20px;
          font-size: 0.9rem;
        }
        
        .status-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
        }
        
        .status-dot.connected {
          background: #4caf50;
          animation: pulse 2s infinite;
        }
        
        .status-dot.disconnected {
          background: #f44336;
        }
        
        .overview-cards {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 1.5rem;
        }
        
        .metric-card {
          background: rgba(26, 34, 53, 0.7);
          border: 1px solid #2a3553;
          border-radius: 12px;
          padding: 1.5rem;
          transition: all 0.3s ease;
        }
        
        .metric-card:hover {
          transform: translateY(-4px);
          box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
          border-color: #00bcd4;
        }
        
        .metric-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1rem;
        }
        
        .metric-header h3 {
          font-size: 0.9rem;
          color: #a8b2d1;
          font-weight: 500;
        }
        
        .status-badge {
          display: flex;
          align-items: center;
          gap: 0.3rem;
          padding: 0.25rem 0.75rem;
          border-radius: 12px;
          font-size: 0.75rem;
          text-transform: uppercase;
          font-weight: 600;
        }
        
        .status-normal {
          background: rgba(76, 175, 80, 0.1);
          color: #4caf50;
        }
        
        .status-warning {
          background: rgba(255, 152, 0, 0.1);
          color: #ff9800;
        }
        
        .status-critical {
          background: rgba(244, 67, 54, 0.1);
          color: #f44336;
        }
        
        .metric-value {
          display: flex;
          align-items: baseline;
          gap: 0.5rem;
          margin-bottom: 0.5rem;
        }
        
        .metric-value .value {
          font-size: 2rem;
          font-weight: 700;
        }
        
        .metric-value .unit {
          font-size: 1rem;
          color: #a8b2d1;
        }
        
        .metric-trend {
          display: flex;
          align-items: center;
          gap: 0.3rem;
          color: #4caf50;
          font-size: 0.9rem;
        }
        
        .units-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
          gap: 1.5rem;
        }
        
        .unit-card {
          background: rgba(26, 34, 53, 0.7);
          border: 1px solid #2a3553;
          border-radius: 12px;
          padding: 1.5rem;
        }
        
        .unit-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1.5rem;
        }
        
        .unit-title {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }
        
        .unit-title h2 {
          font-size: 1.25rem;
          font-weight: 600;
        }
        
        .unit-metrics {
          display: flex;
          flex-direction: column;
          gap: 1rem;
          margin-bottom: 1.5rem;
        }
        
        .metric-row {
          display: flex;
          align-items: center;
          gap: 1rem;
        }
        
        .metric-label {
          flex: 0 0 120px;
          font-size: 0.9rem;
          color: #a8b2d1;
        }
        
        .metric-bar {
          flex: 1;
          height: 8px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 4px;
          overflow: hidden;
        }
        
        .metric-bar-fill {
          height: 100%;
          border-radius: 4px;
          transition: width 0.5s ease;
        }
        
        .metric-percentage {
          flex: 0 0 50px;
          text-align: right;
          font-weight: 600;
        }
        
        .sensor-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 0.75rem;
        }
        
        .sensor-item {
          display: flex;
          flex-direction: column;
          gap: 0.25rem;
          padding: 0.75rem;
          background: rgba(20, 27, 45, 0.5);
          border-radius: 8px;
        }
        
        .sensor-name {
          font-size: 0.8rem;
          color: #a8b2d1;
          text-transform: capitalize;
        }
        
        .sensor-value {
          font-size: 1rem;
          font-weight: 600;
        }
        
        .sensor-value.anomaly {
          color: #f44336;
        }
        
        /* Communications Styles */
        .communications-container {
          display: flex;
          flex-direction: column;
          gap: 2rem;
        }
        
        .comm-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        
        .comm-header h1 {
          font-size: 2rem;
          font-weight: 600;
        }
        
        .comm-stats {
          display: flex;
          gap: 1.5rem;
          font-size: 0.9rem;
          color: #a8b2d1;
        }
        
        .critical-count {
          color: #f44336;
          font-weight: 600;
        }
        
        .comm-list {
          display: flex;
          flex-direction: column;
          gap: 1rem;
          max-height: 70vh;
          overflow-y: auto;
        }
        
        .comm-item {
          background: rgba(26, 34, 53, 0.7);
          border: 1px solid #2a3553;
          border-radius: 12px;
          padding: 1.5rem;
          animation: slideIn 0.3s ease;
        }
        
        .comm-agents {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          font-weight: 600;
        }
        
        .agent-from {
          color: #00bcd4;
        }
        
        .arrow {
          color: #a8b2d1;
        }
        
        .agent-to {
          color: #ff6b35;
        }
        
        .comm-meta {
          display: flex;
          align-items: center;
          gap: 1rem;
        }
        
        .severity-badge {
          padding: 0.25rem 0.75rem;
          border-radius: 12px;
          font-size: 0.75rem;
          color: white;
          text-transform: uppercase;
          font-weight: 600;
        }
        
        .timestamp {
          color: #64748b;
          font-size: 0.85rem;
        }
        
        .comm-message {
          margin: 1rem 0;
          line-height: 1.6;
        }
        
        .comm-action {
          padding-top: 1rem;
          border-top: 1px solid #2a3553;
          color: #a8b2d1;
        }
        
        .empty-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 1rem;
          padding: 4rem;
          color: #64748b;
        }
        
        /* Analytics Styles */
        .analytics-container {
          display: flex;
          flex-direction: column;
          gap: 2rem;
        }
        
        .analytics-header h1 {
          font-size: 2rem;
          font-weight: 600;
          margin-bottom: 0.5rem;
        }
        
        .analytics-header p {
          color: #a8b2d1;
        }
        
        .query-section {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }
        
        .query-input-wrapper {
          display: flex;
          gap: 1rem;
        }
        
        .query-input {
          flex: 1;
          padding: 1rem 1.5rem;
          background: rgba(26, 34, 53, 0.7);
          border: 1px solid #2a3553;
          border-radius: 12px;
          color: #e0e6ed;
          font-size: 1rem;
        }
        
        .query-input:focus {
          outline: none;
          border-color: #00bcd4;
        }
        
        .query-button {
          padding: 1rem 2rem;
          background: linear-gradient(135deg, #00bcd4 0%, #0097a7 100%);
          border: none;
          border-radius: 12px;
          color: white;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.3s ease;
        }
        
        .query-button:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 5px 15px rgba(0, 188, 212, 0.3);
        }
        
        .query-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        
        .query-suggestions {
          display: flex;
          align-items: center;
          gap: 1rem;
        }
        
        .query-suggestions span {
          color: #64748b;
          font-size: 0.9rem;
        }
        
        .suggestion-chip {
          padding: 0.5rem 1rem;
          background: rgba(0, 188, 212, 0.1);
          border: 1px solid rgba(0, 188, 212, 0.3);
          border-radius: 20px;
          color: #00bcd4;
          font-size: 0.85rem;
          cursor: pointer;
          transition: all 0.3s ease;
        }
        
        .suggestion-chip:hover {
          background: rgba(0, 188, 212, 0.2);
          transform: translateY(-2px);
        }
        
        .response-section {
          background: rgba(26, 34, 53, 0.7);
          border: 1px solid #2a3553;
          border-radius: 12px;
          padding: 1.5rem;
          animation: fadeIn 0.5s ease;
        }
        
        .response-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1rem;
          padding-bottom: 1rem;
          border-bottom: 1px solid #2a3553;
        }
        
        .responding-agent {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          color: #00bcd4;
          font-weight: 600;
        }
        
        .confidence {
          color: #4caf50;
          font-size: 0.9rem;
          font-weight: 600;
        }
        
        .response-content {
          line-height: 1.8;
          white-space: pre-wrap;
        }
        
        @keyframes pulse {
          0% {
            box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.4);
          }
          70% {
            box-shadow: 0 0 0 10px rgba(76, 175, 80, 0);
          }
          100% {
            box-shadow: 0 0 0 0 rgba(76, 175, 80, 0);
          }
        }
        
        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateX(-20px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }
        
        @keyframes fadeIn {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }
      `}</style>
    </div>
  );
}

export default App;