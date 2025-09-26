import React, { useState, useEffect, useCallback } from 'react';
import { Activity, Cpu, MessageSquare, BarChart3, AlertCircle, TrendingUp, Server, Gauge, Cloud, Flame, Leaf, Map, Eye } from 'lucide-react';

// Enhanced API Service
const API_BASE = 'http://localhost:8000';

const api = {
  getUnitsStatus: async () => {
    const response = await fetch(`${API_BASE}/api/units/status`);
    return response.json();
  },
  getPublicData: async () => {
    const response = await fetch(`${API_BASE}/api/public-data/current`);
    return response.json();
  },
  getSatelliteData: async (days = 7) => {
    const response = await fetch(`${API_BASE}/api/public-data/satellite/${days}`);
    return response.json();
  },
  optimizeFuelMix: async (totalEnergy, maxCO2) => {
    const params = new URLSearchParams({ total_energy: totalEnergy });
    if (maxCO2) params.append('max_co2', maxCO2);
    const response = await fetch(`${API_BASE}/api/optimization/fuel-mix?${params}`, { method: 'POST' });
    return response.json();
  },
  optimizeProcess: async (includePublicData = true) => {
    const response = await fetch(`${API_BASE}/api/optimization/process?include_public_data=${includePublicData}`, {
      method: 'POST'
    });
    return response.json();
  },
  comprehensiveOptimization: async () => {
    const response = await fetch(`${API_BASE}/api/optimization/comprehensive`, { method: 'POST' });
    return response.json();
  },
  validateChemistry: async (composition) => {
    const params = new URLSearchParams(composition);
    const response = await fetch(`${API_BASE}/api/chemistry/validate?${params}`);
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
  }
};

// Enhanced Metric Card with Public Data
const EnhancedMetricCard = ({ title, value, unit, trend, status, source, confidence }) => {
  const statusColors = {
    normal: '#4caf50',
    warning: '#ff9800',
    critical: '#f44336'
  };

  return (
    <div className="metric-card enhanced">
      <div className="metric-header">
        <h3>{title}</h3>
        <div className="metric-meta">
          {source && (
            <span className="data-source">
              <Cloud size={14} />
              {source}
            </span>
          )}
          <span className={`status-badge status-${status}`}>
            <span className="status-dot" style={{ backgroundColor: statusColors[status] }}></span>
            {status}
          </span>
        </div>
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
      {confidence && (
        <div className="confidence-bar">
          <div className="confidence-fill" style={{ width: `${confidence * 100}%` }}></div>
          <span className="confidence-text">Confidence: {(confidence * 100).toFixed(0)}%</span>
        </div>
      )}
    </div>
  );
};

// Public Data Panel
const PublicDataPanel = ({ publicData, loading }) => {
  if (loading) {
    return <div className="public-data-panel loading">Loading public data...</div>;
  }

  if (!publicData) {
    return <div className="public-data-panel">No public data available</div>;
  }

  const { data, quality_metrics } = publicData;
  const sources = data?.data_sources || {};

  return (
    <div className="public-data-panel">
      <div className="panel-header">
        <h2>
          <Cloud size={20} />
          Public Data Integration
        </h2>
        <div className="quality-score">
          Data Quality: {quality_metrics?.overall_score?.toFixed(0)}%
        </div>
      </div>

      <div className="data-sources-grid">
        {sources.weather && (
          <div className="data-source-card">
            <h4>Weather Conditions</h4>
            <div className="data-items">
              <span>Temperature: {sources.weather.temperature}°C</span>
              <span>Humidity: {sources.weather.humidity}%</span>
              <span>Wind: {sources.weather.wind_speed} m/s</span>
            </div>
          </div>
        )}

        {sources.air_quality && (
          <div className="data-source-card">
            <h4>Air Quality</h4>
            <div className="data-items">
              {Object.entries(sources.air_quality).map(([station, data]) => (
                data && <span key={station}>PM2.5: {data.pm25} µg/m³</span>
              ))}
            </div>
          </div>
        )}

        {sources.satellite_thermal && (
          <div className="data-source-card">
            <h4>Satellite Thermal</h4>
            <div className="data-items">
              <span>Surface Temp: {sources.satellite_thermal.median_temperature?.toFixed(1)}°C</span>
              <span>
                <Eye size={14} />
                Last 7 days
              </span>
            </div>
          </div>
        )}

        {sources.alternative_fuels && (
          <div className="data-source-card">
            <h4>Alternative Fuels</h4>
            <div className="fuel-availability">
              {Object.entries(sources.alternative_fuels.fuels || {}).slice(0, 3).map(([fuel, data]) => (
                <div key={fuel} className="fuel-item">
                  <Leaf size={14} />
                  <span>{fuel.replace('_', ' ')}: {data.availability_tonnes?.toFixed(0)}t</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Optimization Panel
const OptimizationPanel = ({ onOptimize }) => {
  const [optimizationType, setOptimizationType] = useState('fuel');
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [results, setResults] = useState(null);

  const handleOptimize = async () => {
    setIsOptimizing(true);
    try {
      let result;
      switch (optimizationType) {
        case 'fuel':
          result = await api.optimizeFuelMix(200, 75);
          break;
        case 'process':
          result = await api.optimizeProcess(true);
          break;
        case 'comprehensive':
          result = await api.comprehensiveOptimization();
          break;
      }
      setResults(result);
      if (onOptimize) onOptimize(result);
    } catch (error) {
      console.error('Optimization error:', error);
    } finally {
      setIsOptimizing(false);
    }
  };

  return (
    <div className="optimization-panel">
      <div className="panel-header">
        <h2>
          <Flame size={20} />
          AI Optimization Engine
        </h2>
        <select
          value={optimizationType}
          onChange={(e) => setOptimizationType(e.target.value)}
          className="optimization-selector"
        >
          <option value="fuel">Fuel Mix Optimization</option>
          <option value="process">Process Optimization</option>
          <option value="comprehensive">Comprehensive Plant</option>
        </select>
      </div>

      <button
        className={`optimize-button ${isOptimizing ? 'optimizing' : ''}`}
        onClick={handleOptimize}
        disabled={isOptimizing}
      >
        {isOptimizing ? 'Optimizing...' : 'Run Optimization'}
      </button>

      {results && (
        <div className="optimization-results">
          {results.optimal_mix && (
            <div className="fuel-mix-results">
              <h4>Optimal Fuel Mix</h4>
              {Object.entries(results.optimal_mix).map(([fuel, percentage]) => (
                <div key={fuel} className="fuel-bar">
                  <span>{fuel.replace('_', ' ')}</span>
                  <div className="percentage-bar">
                    <div className="fill" style={{ width: `${percentage}%` }}></div>
                  </div>
                  <span>{percentage}%</span>
                </div>
              ))}
              {results.co2_reduction && (
                <div className="co2-reduction">
                  <Leaf size={16} />
                  CO₂ Reduction: {results.co2_reduction.reduction_percentage}%
                </div>
              )}
            </div>
          )}

          {results.optimal_parameters && (
            <div className="process-results">
              <h4>Optimal Parameters</h4>
              {Object.entries(results.optimal_parameters).map(([param, value]) => (
                <div key={param} className="parameter-item">
                  <span>{param.replace('_', ' ')}</span>
                  <span className="value">{typeof value === 'number' ? value.toFixed(2) : value}</span>
                </div>
              ))}
            </div>
          )}

          {results.confidence && (
            <div className="optimization-confidence">
              Confidence: {(results.confidence * 100).toFixed(0)}%
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Main App Component
function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [unitsStatus, setUnitsStatus] = useState([]);
  const [publicData, setPublicData] = useState(null);
  const [communications, setCommunications] = useState([]);
  const [analyticsQuery, setAnalyticsQuery] = useState('');
  const [analyticsResponse, setAnalyticsResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [latestOptimization, setLatestOptimization] = useState(null);

  useEffect(() => {
    // Load initial data
    loadUnitsStatus();
    loadPublicData();
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
        loadUnitsStatus();
      } else if (data.type === 'optimization_update') {
        setLatestOptimization(data.optimization);
      }
    };

    ws.onclose = () => {
      setWsConnected(false);
      console.log('WebSocket disconnected');
    };

    // Periodic refresh
    const interval = setInterval(() => {
      if (activeTab === 'dashboard') {
        loadUnitsStatus();
        loadPublicData();
      }
      if (activeTab === 'communications') loadCommunications();
    }, 10000);

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

  const loadPublicData = async () => {
    try {
      const data = await api.getPublicData();
      setPublicData(data);
    } catch (error) {
      console.error('Error loading public data:', error);
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

  const renderEnhancedDashboard = () => (
    <div className="enhanced-dashboard">
      <div className="dashboard-header">
        <h1>AI-Driven Cement Plant Optimization</h1>
        <div className="header-status">
          <span className={`connection-status ${wsConnected ? 'connected' : 'disconnected'}`}>
            <span className="status-dot"></span>
            {wsConnected ? 'Real-time Connected' : 'Connecting...'}
          </span>
          <span className="data-integration">
            <Cloud size={16} />
            Public Data: Active
          </span>
        </div>
      </div>

      <div className="overview-section">
        <EnhancedMetricCard
          title="Plant Efficiency"
          value="87.5"
          unit="%"
          trend={2.3}
          status="normal"
          source="Satellite"
          confidence={0.92}
        />
        <EnhancedMetricCard
          title="Energy Consumption"
          value="142.8"
          unit="MW"
          trend={-1.2}
          status="normal"
          source="Grid Data"
          confidence={0.95}
        />
        <EnhancedMetricCard
          title="CO₂ Emissions"
          value="825"
          unit="kg/t"
          trend={-3.5}
          status="warning"
          source="CPCB"
          confidence={0.88}
        />
        <EnhancedMetricCard
          title="Alternative Fuel"
          value="35"
          unit="%"
          trend={5.2}
          status="normal"
          source="Calculated"
          confidence={0.91}
        />
      </div>

      <PublicDataPanel publicData={publicData} loading={!publicData} />

      <OptimizationPanel onOptimize={setLatestOptimization} />

      {latestOptimization && (
        <div className="latest-optimization-alert">
          <AlertCircle size={20} />
          <span>New optimization available with {latestOptimization.confidence * 100}% confidence</span>
        </div>
      )}

      <div className="units-grid">
        {unitsStatus.map((unit, idx) => (
          <div key={idx} className="enhanced-unit-card">
            <div className="unit-header">
              <h3>{unit.unit.replace('_', ' ').toUpperCase()}</h3>
              <span className={`status-${unit.status}`}>{unit.status}</span>
            </div>
            <div className="unit-metrics">
              <div className="health-bar">
                <span>Health</span>
                <div className="bar">
                  <div className="fill" style={{ width: `${unit.overall_health}%` }}></div>
                </div>
                <span>{unit.overall_health}%</span>
              </div>
              <div className="efficiency-bar">
                <span>Efficiency</span>
                <div className="bar">
                  <div className="fill" style={{ width: `${unit.efficiency}%` }}></div>
                </div>
                <span>{unit.efficiency}%</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="app">
      <nav className="navbar">
        <div className="nav-brand">
          <Gauge size={28} />
          <span>Cement AI Optimizer 2.0</span>
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
      </nav>

      <main className="main-content">
        {activeTab === 'dashboard' && renderEnhancedDashboard()}
      </main>

      <style jsx>{`
        .app {
          min-height: 100vh;
          background: linear-gradient(135deg, #0a0e1a 0%, #141b2d 100%);
          color: #e0e6ed;
          font-family: 'Inter', -apple-system, sans-serif;
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
        }

        .nav-tab.active {
          background: rgba(0, 188, 212, 0.15);
          color: #00bcd4;
        }

        .main-content {
          padding: 2rem;
          max-width: 1600px;
          margin: 0 auto;
        }

        .enhanced-dashboard {
          display: flex;
          flex-direction: column;
          gap: 2rem;
        }

        .dashboard-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .header-status {
          display: flex;
          gap: 1.5rem;
          align-items: center;
        }

        .connection-status {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.5rem 1rem;
          background: rgba(26, 34, 53, 0.7);
          border-radius: 20px;
        }

        .status-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #4caf50;
          animation: pulse 2s infinite;
        }

        .data-integration {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          color: #00bcd4;
        }

        .overview-section {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 1.5rem;
        }

        .metric-card.enhanced {
          background: rgba(26, 34, 53, 0.7);
          border: 1px solid #2a3553;
          border-radius: 12px;
          padding: 1.5rem;
          transition: all 0.3s ease;
        }

        .metric-meta {
          display: flex;
          gap: 0.5rem;
          align-items: center;
        }

        .data-source {
          display: flex;
          align-items: center;
          gap: 0.25rem;
          font-size: 0.75rem;
          color: #64748b;
        }

        .confidence-bar {
          margin-top: 1rem;
          position: relative;
          height: 4px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 2px;
        }

        .confidence-fill {
          height: 100%;
          background: linear-gradient(90deg, #00bcd4, #0097a7);
          border-radius: 2px;
          transition: width 0.5s ease;
        }

        .confidence-text {
          position: absolute;
          top: -20px;
          right: 0;
          font-size: 0.75rem;
          color: #64748b;
        }

        .public-data-panel {
          background: rgba(26, 34, 53, 0.7);
          border: 1px solid #2a3553;
          border-radius: 12px;
          padding: 1.5rem;
        }

        .panel-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1.5rem;
        }

        .panel-header h2 {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-size: 1.25rem;
        }

        .quality-score {
          padding: 0.5rem 1rem;
          background: rgba(0, 188, 212, 0.1);
          border: 1px solid rgba(0, 188, 212, 0.3);
          border-radius: 20px;
          font-size: 0.9rem;
        }

        .data-sources-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 1rem;
        }

        .data-source-card {
          background: rgba(20, 27, 45, 0.5);
          border-radius: 8px;
          padding: 1rem;
        }

        .data-source-card h4 {
          font-size: 0.9rem;
          margin-bottom: 0.75rem;
          color: #a8b2d1;
        }

        .data-items {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
          font-size: 0.85rem;
        }

        .fuel-item {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .optimization-panel {
          background: rgba(26, 34, 53, 0.7);
          border: 1px solid #2a3553;
          border-radius: 12px;
          padding: 1.5rem;
        }

        .optimization-selector {
          padding: 0.5rem 1rem;
          background: rgba(20, 27, 45, 0.8);
          border: 1px solid #2a3553;
          border-radius: 8px;
          color: #e0e6ed;
        }

        .optimize-button {
          width: 100%;
          padding: 1rem;
          margin: 1rem 0;
          background: linear-gradient(135deg, #00bcd4 0%, #0097a7 100%);
          border: none;
          border-radius: 8px;
          color: white;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .optimize-button:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 5px 15px rgba(0, 188, 212, 0.3);
        }

        .optimization-results {
          margin-top: 1.5rem;
          padding: 1rem;
          background: rgba(20, 27, 45, 0.5);
          border-radius: 8px;
        }

        .fuel-bar {
          display: grid;
          grid-template-columns: 100px 1fr 50px;
          align-items: center;
          gap: 1rem;
          margin: 0.5rem 0;
        }

        .percentage-bar {
          height: 8px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 4px;
          overflow: hidden;
        }

        .percentage-bar .fill {
          height: 100%;
          background: linear-gradient(90deg, #4caf50, #8bc34a);
          border-radius: 4px;
        }

        .co2-reduction {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          margin-top: 1rem;
          padding: 0.75rem;
          background: rgba(76, 175, 80, 0.1);
          border: 1px solid rgba(76, 175, 80, 0.3);
          border-radius: 8px;
          color: #4caf50;
        }

        .parameter-item {
          display: flex;
          justify-content: space-between;
          padding: 0.5rem 0;
          border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }

        .enhanced-unit-card {
          background: rgba(26, 34, 53, 0.7);
          border: 1px solid #2a3553;
          border-radius: 12px;
          padding: 1.5rem;
        }

        .units-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
          gap: 1.5rem;
        }

        .unit-metrics {
          margin-top: 1rem;
        }

        .health-bar, .efficiency-bar {
          display: grid;
          grid-template-columns: 80px 1fr 50px;
          align-items: center;
          gap: 1rem;
          margin: 0.75rem 0;
        }

        .bar {
          height: 8px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 4px;
          overflow: hidden;
        }

        .bar .fill {
          height: 100%;
          background: linear-gradient(90deg, #00bcd4, #0097a7);
          border-radius: 4px;
          transition: width 0.5s ease;
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
      `}</style>
    </div>
  );
}

export default App;