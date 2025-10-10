import React, { useState, useEffect } from 'react';
import { Activity, MessageSquare, BarChart3, Gauge, Cloud, TrendingUp, TrendingDown, AlertCircle, Leaf, Send, Zap, Database, Cpu } from 'lucide-react';
import './App.css';

const API_BASE = 'http://localhost:8000/api';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [wsConnected, setWsConnected] = useState(false);
  const [sensorData, setSensorData] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Setup WebSocket
    const ws = new WebSocket('ws://localhost:8000/ws');

    ws.onopen = () => {
      setWsConnected(true);
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'sensor_update' && data.data) {
        setSensorData(data.data);
        setLoading(false);
      }
    };

    ws.onerror = () => setWsConnected(false);
    ws.onclose = () => setWsConnected(false);

    return () => ws.close();
  }, []);

  const MetricCard = ({ title, value, unit, trend, status, icon: Icon, color }) => (
    <div className={`metric-card ${status}`} style={{ borderLeft: `4px solid ${color}` }}>
      <div className="metric-header">
        <div className="metric-title">
          <Icon size={20} color={color} />
          <h3>{title}</h3>
        </div>
        <span className={`status-badge ${status}`}>{status}</span>
      </div>
      <div className="metric-value">
        <span className="value">{value}</span>
        <span className="unit">{unit}</span>
      </div>
      <div className="metric-trend">
        {trend > 0 ? <TrendingUp size={16} color="#4caf50" /> : <TrendingDown size={16} color="#f44336" />}
        <span style={{ color: trend > 0 ? '#4caf50' : '#f44336' }}>
          {Math.abs(trend)}% from last hour
        </span>
      </div>
    </div>
  );

  const UnitCard = ({ unit, data }) => {
    const unitNames = {
      'precalciner': 'Pre-Calciner',
      'rotary_kiln': 'Rotary Kiln',
      'clinker_cooler': 'Clinker Cooler'
    };

    const getUnitHealth = (sensors) => {
      if (!sensors || sensors.length === 0) return 85;
      const anomalyCount = sensors.filter(s => s.is_anomaly).length;
      return Math.max(50, 100 - (anomalyCount * 10));
    };

    const health = getUnitHealth(data);

    return (
      <div className="unit-card">
        <div className="unit-header">
          <div className="unit-title">
            <Cpu size={24} color="#00bcd4" />
            <h3>{unitNames[unit] || unit}</h3>
          </div>
          <div className={`health-indicator ${health > 80 ? 'good' : health > 60 ? 'warning' : 'critical'}`}>
            <div className="health-value">{health}%</div>
            <div className="health-label">Health</div>
          </div>
        </div>

        <div className="sensors-grid">
          {data && data.slice(0, 6).map((sensor, idx) => (
            <div key={idx} className={`sensor-item ${sensor.is_anomaly ? 'anomaly' : ''}`}>
              <div className="sensor-name">{sensor.sensor_name.replace(/_/g, ' ')}</div>
              <div className="sensor-value">
                {sensor.value.toFixed(2)} <span className="sensor-unit">{sensor.unit_measure}</span>
              </div>
            </div>
          ))}
        </div>

        {data && data.filter(s => s.is_anomaly).length > 0 && (
          <div className="unit-alerts">
            <AlertCircle size={16} color="#ff9800" />
            <span>{data.filter(s => s.is_anomaly).length} anomalies detected</span>
          </div>
        )}
      </div>
    );
  };

  const Dashboard = () => (
    <div className="dashboard">
      <div className="dashboard-hero">
        <div className="hero-content">
          <h1>AI-Driven Cement Plant Optimization</h1>
          <p>Real-time monitoring and intelligent optimization powered by advanced AI</p>
        </div>
        <div className="hero-stats">
          <div className="hero-stat">
            <Zap size={24} color="#00bcd4" />
            <div>
              <div className="stat-value">87.5%</div>
              <div className="stat-label">Plant Efficiency</div>
            </div>
          </div>
          <div className="hero-stat">
            <Database size={24} color="#4caf50" />
            <div>
              <div className="stat-value">{Object.keys(sensorData).length}</div>
              <div className="stat-label">Active Units</div>
            </div>
          </div>
          <div className="hero-stat">
            <Activity size={24} color="#ff9800" />
            <div>
              <div className="stat-value">
                {wsConnected ? 'Live' : 'Offline'}
              </div>
              <div className="stat-label">Status</div>
            </div>
          </div>
        </div>
      </div>

      <div className="metrics-section">
        <h2 className="section-title">Key Performance Indicators</h2>
        <div className="metrics-grid">
          <MetricCard
            title="Plant Efficiency"
            value="87.5"
            unit="%"
            trend={2.3}
            status="normal"
            icon={Zap}
            color="#00bcd4"
          />
          <MetricCard
            title="Energy Consumption"
            value="142.8"
            unit="MW"
            trend={-1.2}
            status="normal"
            icon={Activity}
            color="#4caf50"
          />
          <MetricCard
            title="CO₂ Emissions"
            value="825"
            unit="kg/t"
            trend={-3.5}
            status="warning"
            icon={Cloud}
            color="#ff9800"
          />
          <MetricCard
            title="Alternative Fuel"
            value="35"
            unit="%"
            trend={5.2}
            status="normal"
            icon={Leaf}
            color="#8bc34a"
          />
        </div>
      </div>

      <div className="units-section">
        <h2 className="section-title">Production Units</h2>
        {loading ? (
          <div className="loading-state">
            <div className="spinner"></div>
            <p>Loading sensor data...</p>
          </div>
        ) : (
          <div className="units-grid">
            {Object.entries(sensorData).map(([unit, data]) => (
              <UnitCard key={unit} unit={unit} data={data} />
            ))}
          </div>
        )}
      </div>

      <div className="optimization-section">
        <div className="optimization-card">
          <div className="optimization-header">
            <div>
              <h3>🔥 AI Optimization Engine</h3>
              <p>Intelligent recommendations for optimal plant performance</p>
            </div>
            <button className="optimize-button">
              Run Optimization
            </button>
          </div>
          <div className="optimization-insights">
            <div className="insight-item">
              <div className="insight-icon" style={{ background: 'rgba(0, 188, 212, 0.2)' }}>
                <TrendingUp size={20} color="#00bcd4" />
              </div>
              <div className="insight-content">
                <div className="insight-title">Energy Efficiency</div>
                <div className="insight-value">Potential 8% improvement</div>
              </div>
            </div>
            <div className="insight-item">
              <div className="insight-icon" style={{ background: 'rgba(76, 175, 80, 0.2)' }}>
                <Leaf size={20} color="#4caf50" />
              </div>
              <div className="insight-content">
                <div className="insight-title">Alternative Fuels</div>
                <div className="insight-value">Increase to 45% possible</div>
              </div>
            </div>
            <div className="insight-item">
              <div className="insight-icon" style={{ background: 'rgba(255, 152, 0, 0.2)' }}>
                <AlertCircle size={20} color="#ff9800" />
              </div>
              <div className="insight-content">
                <div className="insight-title">Process Optimization</div>
                <div className="insight-value">3 adjustments recommended</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const Communications = () => (
    <div className="communications">
      <div className="page-header">
        <h1>Agent Communications</h1>
        <p>Real-time coordination between AI agents</p>
      </div>
      <div className="empty-state">
        <MessageSquare size={64} color="#64748b" />
        <h3>No Communications Yet</h3>
        <p>AI agents will communicate here when anomalies are detected</p>
      </div>
    </div>
  );

  const Analytics = () => {
    const [query, setQuery] = useState('');

    const exampleQueries = [
      "What is the current efficiency of the pre-calciner?",
      "How can we optimize the rotary kiln temperature?",
      "What are the main issues in the clinker cooler?",
      "Suggest alternative fuel optimization strategies"
    ];

    return (
      <div className="analytics">
        <div className="page-header">
          <h1>AI Analytics</h1>
          <p>Ask questions about your plant operations in natural language</p>
        </div>

        <div className="query-card">
          <div className="query-input-group">
            <input
              type="text"
              className="query-input"
              placeholder="Ask a question about plant operations..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <button className="query-button">
              <Send size={20} />
              Ask
            </button>
          </div>

          <div className="example-queries">
            <p>Example questions:</p>
            <div className="query-chips">
              {exampleQueries.map((q, idx) => (
                <button key={idx} className="query-chip" onClick={() => setQuery(q)}>
                  {q}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="app">
      <nav className="navbar">
        <div className="nav-brand">
          <Gauge size={32} />
          <div>
            <div className="brand-title">Cement AI Optimizer</div>
            <div className="brand-subtitle">Version 2.0</div>
          </div>
        </div>

        <div className="nav-center">
          <div className={`connection-indicator ${wsConnected ? 'connected' : 'disconnected'}`}>
            <div className="indicator-dot"></div>
            <span>{wsConnected ? 'Real-time Connected' : 'Connecting...'}</span>
          </div>
        </div>

        <div className="nav-tabs">
          <button
            className={`nav-tab ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <Activity size={20} />
            <span>Dashboard</span>
          </button>
          <button
            className={`nav-tab ${activeTab === 'communications' ? 'active' : ''}`}
            onClick={() => setActiveTab('communications')}
          >
            <MessageSquare size={20} />
            <span>Communications</span>
          </button>
          <button
            className={`nav-tab ${activeTab === 'analytics' ? 'active' : ''}`}
            onClick={() => setActiveTab('analytics')}
          >
            <BarChart3 size={20} />
            <span>AI Analytics</span>
          </button>
        </div>
      </nav>

      <main className="main-content">
        {activeTab === 'dashboard' && <Dashboard />}
        {activeTab === 'communications' && <Communications />}
        {activeTab === 'analytics' && <Analytics />}
      </main>
    </div>
  );
}

export default App;