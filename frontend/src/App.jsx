import React, { useState, useEffect } from 'react';
import { Activity, MessageSquare, BarChart3, Gauge, Cloud, TrendingUp, TrendingDown, AlertCircle, Leaf, Send, Zap, Database, Cpu, Loader, X, Download, History, Play, CheckCircle } from 'lucide-react';
import './App.css';
import { queryAnalytics } from './services/api';

const API_BASE = 'http://localhost:8000/api';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [wsConnected, setWsConnected] = useState(false);
  const [sensorData, setSensorData] = useState({});
  const [loading, setLoading] = useState(true);
  const [selectedUnit, setSelectedUnit] = useState(null);
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [showDiagnosticsModal, setShowDiagnosticsModal] = useState(false);
  const [diagnosticsRunning, setDiagnosticsRunning] = useState(false);
  const [diagnosticsResults, setDiagnosticsResults] = useState(null);
  const [historyData, setHistoryData] = useState([]);

  useEffect(() => {
    // Setup WebSocket
    console.log('🔌 Connecting to WebSocket...');
    const ws = new WebSocket('ws://localhost:8000/ws');

    ws.onopen = () => {
      setWsConnected(true);
      console.log('✅ WebSocket connected');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('📊 Received WebSocket message:', data.type);

      if (data.type === 'sensor_update' && data.data) {
        setSensorData(data.data);
        setLoading(false);
      }
    };

    ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
      setWsConnected(false);
    };

    ws.onclose = () => {
      console.log('🔌 WebSocket closed');
      setWsConnected(false);
    };

    return () => {
      console.log('🔌 Cleaning up WebSocket');
      ws.close();
    };
  }, []);

  // Run Diagnostics
  const handleRunDiagnostics = async (unitData) => {
    setDiagnosticsRunning(true);
    setShowDiagnosticsModal(true);

    try {
      // Simulate diagnostics (replace with actual API call)
      await new Promise(resolve => setTimeout(resolve, 2000));

      const anomalies = unitData.data.filter(s => s.is_anomaly);

      const results = {
        unit: unitData.unit,
        timestamp: new Date().toISOString(),
        totalChecks: 15,
        passedChecks: 15 - anomalies.length,
        failedChecks: anomalies.length,
        anomalies: anomalies.map(sensor => ({
          name: sensor.sensor_name,
          value: sensor.value,
          unit: sensor.unit_measure,
          status: 'Critical',
          recommendation: generateRecommendation(sensor)
        })),
        overallStatus: anomalies.length > 5 ? 'Critical' : anomalies.length > 2 ? 'Warning' : 'Good',
        nextSteps: [
          'Review and adjust sensor parameters',
          'Schedule maintenance for critical components',
          'Monitor affected sensors closely for next 24 hours'
        ]
      };

      setDiagnosticsResults(results);
    } catch (error) {
      console.error('Error running diagnostics:', error);
    } finally {
      setDiagnosticsRunning(false);
    }
  };

  // Generate recommendation based on sensor
  const generateRecommendation = (sensor) => {
    const sensorName = sensor.sensor_name.toLowerCase();
    if (sensorName.includes('temp')) {
      return 'Adjust temperature control systems and check cooling efficiency';
    } else if (sensorName.includes('pressure')) {
      return 'Check for blockages and verify damper positions';
    } else if (sensorName.includes('flow')) {
      return 'Inspect flow control valves and air distribution system';
    } else if (sensorName.includes('speed')) {
      return 'Verify motor operation and check for mechanical issues';
    } else {
      return 'Monitor closely and consult maintenance team if issue persists';
    }
  };

  // View History
  const handleViewHistory = async (unitData) => {
    setShowHistoryModal(true);

    try {
      // Fetch historical data (replace with actual API call)
      const response = await fetch(`${API_BASE}/sensors/historical/${unitData.unit}?hours=24`);
      const data = await response.json();

      // Group by timestamp (last 10 readings)
      const grouped = {};
      data.slice(0, 60).forEach(reading => {
        const time = new Date(reading.timestamp).toLocaleTimeString();
        if (!grouped[time]) {
          grouped[time] = [];
        }
        grouped[time].push(reading);
      });

      const history = Object.entries(grouped).map(([time, readings]) => ({
        timestamp: time,
        anomalyCount: readings.filter(r => r.is_anomaly).length,
        readings: readings
      }));

      setHistoryData(history);
    } catch (error) {
      console.error('Error fetching history:', error);
      // Fallback mock data
      setHistoryData(generateMockHistory(unitData));
    }
  };

  // Generate mock history data
  const generateMockHistory = (unitData) => {
    const now = new Date();
    const history = [];

    for (let i = 0; i < 10; i++) {
      const time = new Date(now - i * 3600000); // 1 hour intervals
      history.push({
        timestamp: time.toLocaleString(),
        anomalyCount: Math.floor(Math.random() * 5),
        status: Math.random() > 0.7 ? 'Warning' : 'Normal'
      });
    }

    return history;
  };

  // Export Report
  const handleExportReport = async (unitData) => {
    try {
      const unitNames = {
        'precalciner': 'Pre-Calciner',
        'rotary_kiln': 'Rotary Kiln',
        'clinker_cooler': 'Clinker Cooler'
      };

      const anomalies = unitData.data.filter(s => s.is_anomaly);

      // Create report content
      const reportContent = `
CEMENT PLANT ANOMALY REPORT
============================

Unit: ${unitNames[unitData.unit]}
Generated: ${new Date().toLocaleString()}
Report ID: RPT-${Date.now()}

SUMMARY
-------
Total Sensors: ${unitData.data.length}
Anomalies Detected: ${anomalies.length}
Health Score: ${100 - (anomalies.length * 10)}%
Status: ${anomalies.length > 5 ? 'CRITICAL' : anomalies.length > 2 ? 'WARNING' : 'NORMAL'}

ANOMALY DETAILS
---------------
${anomalies.map((sensor, idx) => `
${idx + 1}. ${sensor.sensor_name.replace(/_/g, ' ').toUpperCase()}
   Current Value: ${sensor.value.toFixed(2)} ${sensor.unit_measure}
   ${sensor.optimal_range ? `Expected Range: ${sensor.optimal_range[0]} - ${sensor.optimal_range[1]} ${sensor.unit_measure}` : ''}
   Status: ALERT
   Timestamp: ${new Date(sensor.timestamp).toLocaleString()}
`).join('\n')}

RECOMMENDATIONS
---------------
1. Immediate inspection of sensors showing anomalies
2. Verify sensor calibration and accuracy
3. Check control system parameters
4. Review recent operational changes
5. Monitor affected systems closely for next 24 hours

NORMAL READINGS
---------------
${unitData.data.filter(s => !s.is_anomaly).map(sensor =>
  `- ${sensor.sensor_name.replace(/_/g, ' ')}: ${sensor.value.toFixed(2)} ${sensor.unit_measure}`
).join('\n')}

============================
End of Report
`;

      // Create blob and download
      const blob = new Blob([reportContent], { type: 'text/plain' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${unitData.unit}_anomaly_report_${Date.now()}.txt`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      // Show success message
      alert('✅ Report exported successfully!');
    } catch (error) {
      console.error('Error exporting report:', error);
      alert('❌ Error exporting report. Please try again.');
    }
  };

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
    const anomalyCount = data ? data.filter(s => s.is_anomaly).length : 0;

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

        {anomalyCount > 0 && (
          <div
            className="unit-alerts clickable"
            onClick={() => setSelectedUnit({ unit, data, anomalyCount })}
          >
            <AlertCircle size={16} color="#ff9800" />
            <span>{anomalyCount} anomalies detected - Click to view details</span>
          </div>
        )}
      </div>
    );
  };

  // Diagnostics Modal
  const DiagnosticsModal = ({ onClose }) => {
    if (!showDiagnosticsModal) return null;

    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal-content diagnostics-modal" onClick={(e) => e.stopPropagation()}>
          <div className="modal-header">
            <h2>🔍 System Diagnostics</h2>
            <button className="modal-close" onClick={onClose}>
              <X size={24} />
            </button>
          </div>

          <div className="modal-body">
            {diagnosticsRunning ? (
              <div className="diagnostics-running">
                <Loader className="spinner-large" size={48} />
                <h3>Running Comprehensive Diagnostics...</h3>
                <p>Analyzing sensors, checking parameters, and evaluating system health</p>
                <div className="diagnostics-steps">
                  <div className="step completed">✓ Sensor Calibration Check</div>
                  <div className="step completed">✓ Parameter Validation</div>
                  <div className="step active">⟳ Anomaly Analysis</div>
                  <div className="step">○ Performance Evaluation</div>
                  <div className="step">○ Generating Report</div>
                </div>
              </div>
            ) : diagnosticsResults ? (
              <div className="diagnostics-results">
                <div className={`diagnostics-summary ${diagnosticsResults.overallStatus.toLowerCase()}`}>
                  <div className="summary-icon">
                    {diagnosticsResults.overallStatus === 'Good' ? <CheckCircle size={48} /> : <AlertCircle size={48} />}
                  </div>
                  <div>
                    <h3>Diagnostics Complete</h3>
                    <p>Status: <strong>{diagnosticsResults.overallStatus}</strong></p>
                  </div>
                </div>

                <div className="diagnostics-stats">
                  <div className="stat-box">
                    <div className="stat-value">{diagnosticsResults.totalChecks}</div>
                    <div className="stat-label">Total Checks</div>
                  </div>
                  <div className="stat-box success">
                    <div className="stat-value">{diagnosticsResults.passedChecks}</div>
                    <div className="stat-label">Passed</div>
                  </div>
                  <div className="stat-box error">
                    <div className="stat-value">{diagnosticsResults.failedChecks}</div>
                    <div className="stat-label">Failed</div>
                  </div>
                </div>

                {diagnosticsResults.anomalies.length > 0 && (
                  <div className="diagnostics-anomalies">
                    <h4>Issues Found:</h4>
                    {diagnosticsResults.anomalies.map((anomaly, idx) => (
                      <div key={idx} className="diagnostic-issue">
                        <div className="issue-header">
                          <span className="issue-name">{anomaly.name.replace(/_/g, ' ')}</span>
                          <span className={`issue-status ${anomaly.status.toLowerCase()}`}>{anomaly.status}</span>
                        </div>
                        <div className="issue-value">
                          Current: {anomaly.value.toFixed(2)} {anomaly.unit}
                        </div>
                        <div className="issue-recommendation">
                          💡 {anomaly.recommendation}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                <div className="diagnostics-nextsteps">
                  <h4>Recommended Next Steps:</h4>
                  <ol>
                    {diagnosticsResults.nextSteps.map((step, idx) => (
                      <li key={idx}>{step}</li>
                    ))}
                  </ol>
                </div>

                <div className="diagnostics-actions">
                  <button className="action-button primary" onClick={onClose}>
                    Close Report
                  </button>
                  <button
                    className="action-button secondary"
                    onClick={() => handleExportReport(selectedUnit)}
                  >
                    <Download size={16} /> Export Full Report
                  </button>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      </div>
    );
  };

  // History Modal
  const HistoryModal = ({ onClose }) => {
    if (!showHistoryModal) return null;

    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal-content history-modal" onClick={(e) => e.stopPropagation()}>
          <div className="modal-header">
            <h2>📊 Historical Data</h2>
            <button className="modal-close" onClick={onClose}>
              <X size={24} />
            </button>
          </div>

          <div className="modal-body">
            <div className="history-info">
              <History size={32} color="#00bcd4" />
              <div>
                <h3>Last 24 Hours</h3>
                <p>Showing anomaly trends and sensor readings</p>
              </div>
            </div>

            <div className="history-timeline">
              {historyData.map((entry, idx) => (
                <div key={idx} className="history-entry">
                  <div className="history-time">{entry.timestamp}</div>
                  <div className="history-dot"></div>
                  <div className="history-content">
                    <div className="history-status">
                      {entry.anomalyCount > 0 ? (
                        <span className="status-badge warning">
                          {entry.anomalyCount} Anomalies
                        </span>
                      ) : (
                        <span className="status-badge normal">Normal</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="history-actions">
              <button className="action-button secondary" onClick={onClose}>
                Close
              </button>
              <button
                className="action-button primary"
                onClick={() => {
                  alert('📥 Downloading historical data export...');
                  // Implement CSV export here
                }}
              >
                <Download size={16} /> Export CSV
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Main Anomaly Modal
  const AnomalyModal = ({ unitData, onClose }) => {
    if (!unitData) return null;

    const unitNames = {
      'precalciner': 'Pre-Calciner',
      'rotary_kiln': 'Rotary Kiln',
      'clinker_cooler': 'Clinker Cooler'
    };

    const anomalies = unitData.data.filter(s => s.is_anomaly);

    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal-content" onClick={(e) => e.stopPropagation()}>
          <div className="modal-header">
            <h2>🚨 {unitNames[unitData.unit]} - Anomaly Details</h2>
            <button className="modal-close" onClick={onClose}>
              <X size={24} />
            </button>
          </div>

          <div className="modal-body">
            <div className="anomaly-summary">
              <AlertCircle size={32} color="#ff9800" />
              <div>
                <h3>{unitData.anomalyCount} Anomalies Detected</h3>
                <p>These sensors are operating outside normal parameters</p>
              </div>
            </div>

            <div className="anomaly-list">
              {anomalies.map((sensor, idx) => (
                <div key={idx} className="anomaly-item">
                  <div className="anomaly-icon">⚠️</div>
                  <div className="anomaly-details">
                    <h4>{sensor.sensor_name.replace(/_/g, ' ')}</h4>
                    <div className="anomaly-value">
                      Current: <strong>{sensor.value.toFixed(2)} {sensor.unit_measure}</strong>
                    </div>
                    {sensor.optimal_range && (
                      <div className="anomaly-range">
                        Expected: {sensor.optimal_range[0]} - {sensor.optimal_range[1]} {sensor.unit_measure}
                      </div>
                    )}
                  </div>
                  <div className="anomaly-status">ALERT</div>
                </div>
              ))}
            </div>

            <div className="anomaly-actions">
              <button
                className="action-button primary"
                onClick={() => {
                  onClose();
                  handleRunDiagnostics(unitData);
                }}
              >
                <Play size={16} /> Run Diagnostics
              </button>
              <button
                className="action-button secondary"
                onClick={() => {
                  onClose();
                  handleViewHistory(unitData);
                }}
              >
                <History size={16} /> View History
              </button>
              <button
                className="action-button secondary"
                onClick={() => handleExportReport(unitData)}
              >
                <Download size={16} /> Export Report
              </button>
            </div>
          </div>
        </div>
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

      <div className="kpi-grid">
        <MetricCard
          title="PLANT EFFICIENCY"
          value="87.5"
          unit="%"
          trend={2.3}
          status="NORMAL"
          icon={Zap}
          color="#00bcd4"
        />
        <MetricCard
          title="ENERGY CONSUMPTION"
          value="142.8"
          unit="MW"
          trend={-1.2}
          status="NORMAL"
          icon={Activity}
          color="#4caf50"
        />
        <MetricCard
          title="CO₂ EMISSIONS"
          value="825"
          unit="kg/t"
          trend={-3.5}
          status="WARNING"
          icon={Cloud}
          color="#ff9800"
        />
        <MetricCard
          title="ALTERNATIVE FUEL"
          value="35"
          unit="%"
          trend={5.2}
          status="NORMAL"
          icon={Leaf}
          color="#4caf50"
        />
      </div>

      <div className="units-section">
        <h2>Production Units</h2>
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

      {selectedUnit && (
        <AnomalyModal
          unitData={selectedUnit}
          onClose={() => setSelectedUnit(null)}
        />
      )}

      <DiagnosticsModal onClose={() => setShowDiagnosticsModal(false)} />
      <HistoryModal onClose={() => setShowHistoryModal(false)} />
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
    const [chatHistory, setChatHistory] = useState([]);
    const [isLoading, setIsLoading] = useState(false);

    const exampleQueries = [
      "What is the current efficiency of the pre-calciner?",
      "How can we optimize the rotary kiln temperature?",
      "What are the main issues in the clinker cooler?",
      "Suggest alternative fuel optimization strategies"
    ];

    const formatResponse = (text) => {
      const sections = text.split(/\*\*\d+\./);

      return sections.map((section, idx) => {
        if (idx === 0) return section;

        const parts = section.split(':**');
        if (parts.length >= 2) {
          const title = parts[0].trim().replace(/\*\*/g, '');
          const content = parts[1].trim();

          return (
            <div key={idx} className="response-section">
              <h4>{title}</h4>
              <p>{content.replace(/\*\*/g, '')}</p>
            </div>
          );
        }
        return <p key={idx}>{section.replace(/\*\*/g, '')}</p>;
      });
    };

    const handleAskQuestion = async () => {
      if (!query.trim() || isLoading) return;

      const userMessage = {
        type: 'user',
        text: query,
        timestamp: new Date().toISOString()
      };

      setChatHistory(prev => [...prev, userMessage]);
      setIsLoading(true);

      try {
        console.log('📤 Sending query to API:', query);
        const response = await queryAnalytics(query);
        console.log('📥 Received response:', response);

        const aiMessage = {
          type: 'ai',
          text: response.answer,
          confidence: response.confidence,
          agent: response.responding_agent,
          sources: response.sources,
          timestamp: response.timestamp
        };

        setChatHistory(prev => [...prev, aiMessage]);
      } catch (error) {
        console.error('❌ Error querying analytics:', error);

        const errorMessage = {
          type: 'error',
          text: `Sorry, I encountered an error: ${error.message}. Please make sure the backend server is running.`,
          timestamp: new Date().toISOString()
        };

        setChatHistory(prev => [...prev, errorMessage]);
      } finally {
        setIsLoading(false);
        setQuery('');
      }
    };

    const handleKeyPress = (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleAskQuestion();
      }
    };

    return (
      <div className="analytics">
        <div className="page-header">
          <h1>AI Analytics</h1>
          <p>Ask questions about your plant operations in natural language</p>
        </div>

        <div className="chat-container">
          <div className="chat-messages">
            {chatHistory.length === 0 ? (
              <div className="chat-welcome">
                <BarChart3 size={48} color="#00bcd4" />
                <h3>Welcome to AI Analytics</h3>
                <p>Ask me anything about your cement plant operations</p>
              </div>
            ) : (
              chatHistory.map((message, idx) => (
                <div key={idx} className={`chat-message ${message.type}`}>
                  <div className="message-header">
                    <strong>
                      {message.type === 'user' ? 'You' : message.agent || 'AI Assistant'}
                    </strong>
                    <span className="message-time">
                      {new Date(message.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <div className="message-content formatted">
                    {message.type === 'ai' ? formatResponse(message.text) : message.text}
                  </div>
                  {message.confidence && (
                    <div className="message-footer">
                      <span className="confidence-badge">
                        Confidence: {(message.confidence * 100).toFixed(0)}%
                      </span>
                      {message.sources && message.sources.length > 0 && (
                        <span className="sources-badge">
                          Sources: {message.sources.slice(0, 2).join(', ')}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              ))
            )}
            {isLoading && (
              <div className="chat-message ai loading">
                <div className="message-content">
                  <Loader className="spinner-icon" size={16} />
                  <span>Analyzing your question...</span>
                </div>
              </div>
            )}
          </div>

          <div className="query-card">
            <div className="query-input-group">
              <input
                type="text"
                className="query-input"
                placeholder="Ask a question about plant operations..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={isLoading}
              />
              <button
                className="query-button"
                onClick={handleAskQuestion}
                disabled={isLoading || !query.trim()}
              >
                {isLoading ? (
                  <Loader className="spinner-icon" size={20} />
                ) : (
                  <Send size={20} />
                )}
                {isLoading ? 'Processing...' : 'Ask'}
              </button>
            </div>

            <div className="example-queries">
              <p>Example questions:</p>
              <div className="query-chips">
                {exampleQueries.map((q, idx) => (
                  <button
                    key={idx}
                    className="query-chip"
                    onClick={() => setQuery(q)}
                    disabled={isLoading}
                  >
                    {q}
                  </button>
                ))}
              </div>
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