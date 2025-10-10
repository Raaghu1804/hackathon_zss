import React, { useState, useEffect } from 'react';
import { Activity, MessageSquare, BarChart3, Gauge, Cloud, TrendingUp, TrendingDown, AlertCircle, Leaf, Send } from 'lucide-react';
import * as api from './services/api';
import './App.css';

// Enhanced Metric Card Component
const EnhancedMetricCard = ({ title, value, unit, trend, status, source, confidence }) => (
  <div className="metric-card enhanced">
    <div className="metric-header">
      <h3>{title}</h3>
      <span className={`status-badge ${status}`}>{status}</span>
    </div>
    <div className="metric-value">
      <span className="value">{value}</span>
      <span className="unit">{unit}</span>
    </div>
    <div className="metric-meta">
      <div className="trend">
        {trend > 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
        <span>{Math.abs(trend)}%</span>
      </div>
      <div className="data-source">
        <Cloud size={12} />
        <span>{source}</span>
      </div>
    </div>
    <div className="confidence-bar">
      <div className="confidence-fill" style={{ width: `${confidence * 100}%` }}></div>
      <span className="confidence-text">Confidence: {(confidence * 100).toFixed(0)}%</span>
    </div>
  </div>
);

// Public Data Panel Component
const PublicDataPanel = ({ publicData, loading }) => {
  if (loading) {
    return (
      <div className="public-data-panel">
        <div className="panel-header">
          <h2><Cloud size={20} /> Public Data Integration</h2>
        </div>
        <div className="loading-spinner">Loading public data...</div>
      </div>
    );
  }

  if (!publicData) return null;

  return (
    <div className="public-data-panel">
      <div className="panel-header">
        <h2><Cloud size={20} /> Public Data Integration</h2>
        <span className="quality-score">Quality Score: {(publicData.confidence_score * 100).toFixed(0)}%</span>
      </div>
      <div className="data-grid">
        {publicData.weather && (
          <div className="data-card">
            <h4>Weather Conditions</h4>
            <p>Temperature: {publicData.weather.temperature}°C</p>
            <p>Humidity: {publicData.weather.humidity}%</p>
            <p>Wind Speed: {publicData.weather.wind_speed} m/s</p>
          </div>
        )}
        {publicData.fuel_prices && (
          <div className="data-card">
            <h4>Fuel Prices</h4>
            <p>Coal: ₹{publicData.fuel_prices.coal}/ton</p>
            <p>Pet Coke: ₹{publicData.fuel_prices.petcoke}/ton</p>
          </div>
        )}
        {publicData.grid_data && (
          <div className="data-card">
            <h4>Grid Information</h4>
            <p>Current Load: {publicData.grid_data.current_load} MW</p>
            <p>Tariff: ₹{publicData.grid_data.tariff}/kWh</p>
          </div>
        )}
      </div>
    </div>
  );
};

// Optimization Panel Component
const OptimizationPanel = ({ onOptimize }) => {
  const [selectedOptimization, setSelectedOptimization] = useState('comprehensive');
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [results, setResults] = useState(null);

  const optimizationTypes = [
    { value: 'fuel_mix', label: 'Fuel Mix Optimization' },
    { value: 'process', label: 'Process Parameters' },
    { value: 'comprehensive', label: 'Comprehensive Plant' }
  ];

  const handleOptimize = async () => {
    setIsOptimizing(true);
    try {
      let result;
      if (selectedOptimization === 'fuel_mix') {
        result = await api.optimizeFuelMix();
      } else if (selectedOptimization === 'process') {
        result = await api.optimizeWithPublicData();
      } else {
        result = await api.comprehensiveOptimization();
      }
      setResults(result);
      if (onOptimize) onOptimize(result);
    } catch (error) {
      console.error('Optimization error:', error);
    }
    setIsOptimizing(false);
  };

  return (
    <div className="optimization-panel">
      <div className="panel-header">
        <h2>🔥 AI Optimization Engine</h2>
        <select
          value={selectedOptimization}
          onChange={(e) => setSelectedOptimization(e.target.value)}
          className="optimization-select"
        >
          {optimizationTypes.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
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

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setWsConnected(false);
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
          <span className={`connection-status ${publicData ? 'connected' : 'disconnected'}`}>
            <Cloud size={16} />
            {publicData ? 'Public Data: Active' : 'Loading public data...'}
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
          <span>New optimization available with {(latestOptimization.confidence * 100).toFixed(0)}% confidence</span>
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

  const renderCommunications = () => (
    <div className="communications-page">
      <div className="page-header">
        <h1>Agent Communications</h1>
        <p>Real-time communication between AI agents monitoring plant operations</p>
      </div>

      <div className="communications-stats">
        <div className="stat-card">
          <h3>Total Communications</h3>
          <span className="stat-value">{communications.length}</span>
        </div>
        <div className="stat-card">
          <h3>Critical Alerts</h3>
          <span className="stat-value critical">
            {communications.filter(c => c.severity === 'critical').length}
          </span>
        </div>
        <div className="stat-card">
          <h3>Warnings</h3>
          <span className="stat-value warning">
            {communications.filter(c => c.severity === 'warning').length}
          </span>
        </div>
      </div>

      <div className="communications-list">
        {communications.length === 0 ? (
          <div className="empty-state">
            <MessageSquare size={48} />
            <p>No communications yet. AI agents will communicate when anomalies are detected.</p>
          </div>
        ) : (
          communications.map((comm, idx) => (
            <div key={idx} className={`communication-card severity-${comm.severity}`}>
              <div className="comm-header">
                <div className="comm-agents">
                  <span className="agent-badge">{comm.from_agent}</span>
                  <span className="arrow">→</span>
                  <span className="agent-badge">{comm.to_agent}</span>
                </div>
                <span className={`severity-badge ${comm.severity}`}>
                  {comm.severity}
                </span>
              </div>
              <div className="comm-content">
                <p className="message">{comm.message}</p>
                {comm.action_taken && (
                  <div className="action-taken">
                    <strong>Action Taken:</strong> {comm.action_taken}
                  </div>
                )}
              </div>
              <div className="comm-footer">
                <span className="timestamp">
                  {new Date(comm.timestamp).toLocaleString()}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );

  const renderAnalytics = () => (
    <div className="analytics-page">
      <div className="page-header">
        <h1>AI Analytics</h1>
        <p>Ask questions about your plant operations in natural language</p>
      </div>

      <div className="query-section">
        <div className="query-input-group">
          <input
            type="text"
            className="query-input"
            placeholder="Ask a question about plant operations..."
            value={analyticsQuery}
            onChange={(e) => setAnalyticsQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleAnalyticsQuery()}
          />
          <button
            className="query-button"
            onClick={handleAnalyticsQuery}
            disabled={loading || !analyticsQuery.trim()}
          >
            <Send size={20} />
            {loading ? 'Processing...' : 'Ask'}
          </button>
        </div>

        <div className="example-queries">
          <p>Example queries:</p>
          <button onClick={() => setAnalyticsQuery("What is the current efficiency of the pre-calciner?")}>
            Current pre-calciner efficiency
          </button>
          <button onClick={() => setAnalyticsQuery("How can we optimize the rotary kiln temperature?")}>
            Optimize kiln temperature
          </button>
          <button onClick={() => setAnalyticsQuery("What are the main issues in the clinker cooler?")}>
            Clinker cooler issues
          </button>
        </div>
      </div>

      {analyticsResponse && (
        <div className="analytics-response">
          <div className="response-header">
            <h3>AI Response</h3>
            <span className="confidence-badge">
              Confidence: {(analyticsResponse.confidence * 100).toFixed(0)}%
            </span>
          </div>
          <div className="response-content">
            <p>{analyticsResponse.answer}</p>
          </div>
          {analyticsResponse.sources && analyticsResponse.sources.length > 0 && (
            <div className="response-sources">
              <h4>Sources:</h4>
              <ul>
                {analyticsResponse.sources.map((source, idx) => (
                  <li key={idx}>{source}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
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
        {activeTab === 'communications' && renderCommunications()}
        {activeTab === 'analytics' && renderAnalytics()}
      </main>
    </div>
  );
}

export default App;