// frontend/src/components/PredictiveMaintenance.jsx

import React, { useState, useEffect } from 'react';
import { AlertTriangle, Calendar, Clock, DollarSign, Wrench, TrendingDown, CheckCircle } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

const PredictiveMaintenance = () => {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedUnit, setSelectedUnit] = useState('all');

  useEffect(() => {
    loadDashboard();
    const interval = setInterval(loadDashboard, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const loadDashboard = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/maintenance/dashboard`);
      const data = await response.json();
      setDashboard(data);
      setLoading(false);
    } catch (error) {
      console.error('Error loading maintenance dashboard:', error);
      setLoading(false);
    }
  };

  const getUrgencyColor = (urgency) => {
    const colors = {
      critical: '#f44336',
      high: '#ff9800',
      medium: '#ffeb3b',
      low: '#4caf50'
    };
    return colors[urgency] || '#64748b';
  };

  const getUrgencyIcon = (urgency) => {
    if (urgency === 'critical' || urgency === 'high') {
      return <AlertTriangle size={20} />;
    }
    return <Wrench size={20} />;
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading predictive maintenance data...</p>
      </div>
    );
  }

  return (
    <div className="predictive-maintenance">
      <div className="pm-header">
        <div className="header-content">
          <h1>🔮 Predictive Maintenance</h1>
          <p>AI-powered forecasting to prevent unplanned downtime</p>
        </div>
        <div className="header-stats">
          <div className="stat-card critical">
            <AlertTriangle size={24} />
            <div>
              <div className="stat-value">{dashboard?.critical_maintenance?.length || 0}</div>
              <div className="stat-label">Critical Items</div>
            </div>
          </div>
          <div className="stat-card warning">
            <Clock size={24} />
            <div>
              <div className="stat-value">{dashboard?.total_estimated_downtime_hours?.toFixed(0) || 0}h</div>
              <div className="stat-label">Est. Downtime</div>
            </div>
          </div>
          <div className="stat-card cost">
            <DollarSign size={24} />
            <div>
              <div className="stat-value">${(dashboard?.total_cost_impact / 1000000)?.toFixed(2) || 0}M</div>
              <div className="stat-label">Cost Impact</div>
            </div>
          </div>
        </div>
      </div>

      {/* Unit Filters */}
      <div className="unit-filters">
        <button
          className={`filter-btn ${selectedUnit === 'all' ? 'active' : ''}`}
          onClick={() => setSelectedUnit('all')}
        >
          All Units
        </button>
        <button
          className={`filter-btn ${selectedUnit === 'precalciner' ? 'active' : ''}`}
          onClick={() => setSelectedUnit('precalciner')}
        >
          Pre-Calciner
        </button>
        <button
          className={`filter-btn ${selectedUnit === 'rotary_kiln' ? 'active' : ''}`}
          onClick={() => setSelectedUnit('rotary_kiln')}
        >
          Rotary Kiln
        </button>
        <button
          className={`filter-btn ${selectedUnit === 'clinker_cooler' ? 'active' : ''}`}
          onClick={() => setSelectedUnit('clinker_cooler')}
        >
          Clinker Cooler
        </button>
      </div>

      {/* Critical Maintenance Items */}
      <div className="maintenance-section">
        <h2>🚨 Priority Maintenance Schedule</h2>
        <div className="maintenance-grid">
          {dashboard?.critical_maintenance
            ?.filter(item => selectedUnit === 'all' || item.unit === selectedUnit)
            ?.slice(0, 8)
            ?.map((item, idx) => (
            <div key={idx} className="maintenance-card">
              <div className="card-header">
                <div className="component-info">
                  {getUrgencyIcon(item.urgency)}
                  <div>
                    <h3>{item.component?.replace(/_/g, ' ')}</h3>
                    <span className="unit-badge">{item.unit?.replace(/_/g, ' ')}</span>
                  </div>
                </div>
                <span
                  className="urgency-badge"
                  style={{ backgroundColor: getUrgencyColor(item.urgency) }}
                >
                  {item.urgency}
                </span>
              </div>

              <div className="health-score">
                <div className="score-label">Health Score</div>
                <div className="score-bar">
                  <div
                    className="score-fill"
                    style={{
                      width: `${item.current_score * 100}%`,
                      backgroundColor: item.current_score > 0.7 ? '#4caf50' :
                                     item.current_score > 0.5 ? '#ff9800' : '#f44336'
                    }}
                  />
                </div>
                <div className="score-value">{(item.current_score * 100).toFixed(0)}%</div>
              </div>

              <div className="maintenance-details">
                <div className="detail-item">
                  <Calendar size={16} />
                  <span>Schedule in {item.recommended_window_days} days</span>
                </div>
                <div className="detail-item">
                  <Clock size={16} />
                  <span>Duration: {item.estimated_duration_hours}h</span>
                </div>
              </div>

              {item.preventive_action && (
                <div className="preventive-action">
                  <strong>Action:</strong> {item.preventive_action}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Unit-Specific Forecasts */}
      <div className="forecasts-section">
        <h2>📊 72-Hour Forecast by Unit</h2>
        <div className="forecasts-grid">
          {dashboard?.unit_forecasts && Object.entries(dashboard.unit_forecasts)
            .filter(([unit]) => selectedUnit === 'all' || unit === selectedUnit)
            .map(([unit, forecast]) => (
            <div key={unit} className="forecast-card">
              <div className="forecast-header">
                <h3>{unit.replace(/_/g, ' ')}</h3>
                <span className="confidence-badge">
                  {(forecast.confidence_score * 100).toFixed(0)}% confidence
                </span>
              </div>

              {forecast.predicted_anomalies?.length > 0 ? (
                <div className="anomalies-list">
                  <h4>Predicted Anomalies</h4>
                  {forecast.predicted_anomalies.slice(0, 3).map((anomaly, idx) => (
                    <div key={idx} className="anomaly-item">
                      <div className="anomaly-header">
                        <span className="sensor-name">{anomaly.sensor_name}</span>
                        <span className="time-estimate">in {anomaly.estimated_time_hours}h</span>
                      </div>
                      <div className="anomaly-details">
                        <span
                          className="severity-tag"
                          style={{ backgroundColor: getUrgencyColor(anomaly.severity) }}
                        >
                          {anomaly.severity}
                        </span>
                        <span className="probability">{(anomaly.probability * 100).toFixed(0)}% likely</span>
                      </div>
                      <p className="root-cause">{anomaly.root_cause}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="no-anomalies">
                  <CheckCircle size={48} color="#4caf50" />
                  <p>No anomalies predicted in next 72 hours</p>
                </div>
              )}

              {/* Maintenance Scores */}
              {forecast.maintenance_scores && (
                <div className="scores-section">
                  <h4>Component Health</h4>
                  {Object.entries(forecast.maintenance_scores).map(([component, score]) => (
                    <div key={component} className="score-row">
                      <span className="component-name">{component.replace(/_/g, ' ')}</span>
                      <div className="mini-score-bar">
                        <div
                          className="mini-fill"
                          style={{
                            width: `${score * 100}%`,
                            backgroundColor: score > 0.7 ? '#4caf50' : score > 0.5 ? '#ff9800' : '#f44336'
                          }}
                        />
                      </div>
                      <span className="score-text">{(score * 100).toFixed(0)}%</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      <style jsx>{`
        .predictive-maintenance {
          padding: 2rem;
          max-width: 1600px;
          margin: 0 auto;
        }

        .pm-header {
          margin-bottom: 2rem;
        }

        .header-content h1 {
          font-size: 2rem;
          margin-bottom: 0.5rem;
        }

        .header-content p {
          color: #a8b2d1;
        }

        .header-stats {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 1rem;
          margin-top: 1.5rem;
        }

        .stat-card {
          display: flex;
          align-items: center;
          gap: 1rem;
          padding: 1.5rem;
          background: rgba(26, 34, 53, 0.7);
          border: 1px solid #2a3553;
          border-radius: 12px;
        }

        .stat-card.critical {
          border-color: #f44336;
        }

        .stat-card.warning {
          border-color: #ff9800;
        }

        .stat-card.cost {
          border-color: #00bcd4;
        }

        .stat-value {
          font-size: 1.75rem;
          font-weight: 700;
        }

        .stat-label {
          color: #a8b2d1;
          font-size: 0.9rem;
        }

        .unit-filters {
          display: flex;
          gap: 0.75rem;
          margin-bottom: 2rem;
        }

        .filter-btn {
          padding: 0.75rem 1.5rem;
          background: rgba(26, 34, 53, 0.7);
          border: 1px solid #2a3553;
          border-radius: 8px;
          color: #a8b2d1;
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .filter-btn:hover {
          border-color: #00bcd4;
          color: #00bcd4;
        }

        .filter-btn.active {
          background: rgba(0, 188, 212, 0.2);
          border-color: #00bcd4;
          color: #00bcd4;
        }

        .maintenance-section {
          margin-bottom: 3rem;
        }

        .maintenance-section h2 {
          margin-bottom: 1.5rem;
          font-size: 1.5rem;
        }

        .maintenance-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
          gap: 1.5rem;
        }

        .maintenance-card {
          background: rgba(26, 34, 53, 0.7);
          border: 1px solid #2a3553;
          border-radius: 12px;
          padding: 1.5rem;
          transition: all 0.3s ease;
        }

        .maintenance-card:hover {
          transform: translateY(-4px);
          box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }

        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: start;
          margin-bottom: 1rem;
        }

        .component-info {
          display: flex;
          gap: 0.75rem;
          align-items: start;
        }

        .component-info h3 {
          font-size: 1.1rem;
          margin-bottom: 0.25rem;
          text-transform: capitalize;
        }

        .unit-badge {
          display: inline-block;
          padding: 0.15rem 0.5rem;
          background: rgba(0, 188, 212, 0.1);
          border: 1px solid rgba(0, 188, 212, 0.3);
          border-radius: 4px;
          font-size: 0.75rem;
          color: #00bcd4;
          text-transform: capitalize;
        }

        .urgency-badge {
          padding: 0.25rem 0.75rem;
          border-radius: 12px;
          font-size: 0.75rem;
          font-weight: 600;
          text-transform: uppercase;
          color: white;
        }

        .health-score {
          margin: 1rem 0;
        }

        .score-label {
          font-size: 0.9rem;
          color: #a8b2d1;
          margin-bottom: 0.5rem;
        }

        .score-bar {
          height: 8px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 4px;
          overflow: hidden;
          margin-bottom: 0.5rem;
        }

        .score-fill {
          height: 100%;
          transition: width 0.5s ease;
        }

        .score-value {
          font-size: 0.9rem;
          font-weight: 600;
        }

        .maintenance-details {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
          margin: 1rem 0;
        }

        .detail-item {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          color: #a8b2d1;
          font-size: 0.9rem;
        }

        .preventive-action {
          margin-top: 1rem;
          padding: 0.75rem;
          background: rgba(0, 188, 212, 0.1);
          border-left: 3px solid #00bcd4;
          border-radius: 4px;
          font-size: 0.9rem;
          line-height: 1.4;
        }

        .forecasts-section h2 {
          margin-bottom: 1.5rem;
          font-size: 1.5rem;
        }

        .forecasts-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
          gap: 1.5rem;
        }

        .forecast-card {
          background: rgba(26, 34, 53, 0.7);
          border: 1px solid #2a3553;
          border-radius: 12px;
          padding: 1.5rem;
        }

        .forecast-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1.5rem;
          padding-bottom: 1rem;
          border-bottom: 1px solid #2a3553;
        }

        .forecast-header h3 {
          font-size: 1.25rem;
          text-transform: capitalize;
        }

        .confidence-badge {
          padding: 0.25rem 0.75rem;
          background: rgba(76, 175, 80, 0.1);
          border: 1px solid rgba(76, 175, 80, 0.3);
          border-radius: 12px;
          font-size: 0.85rem;
          color: #4caf50;
        }

        .anomalies-list h4 {
          margin-bottom: 1rem;
          color: #a8b2d1;
        }

        .anomaly-item {
          margin-bottom: 1rem;
          padding: 1rem;
          background: rgba(20, 27, 45, 0.5);
          border-radius: 8px;
          border-left: 3px solid #ff9800;
        }

        .anomaly-header {
          display: flex;
          justify-content: space-between;
          margin-bottom: 0.5rem;
        }

        .sensor-name {
          font-weight: 600;
        }

        .time-estimate {
          color: #ff9800;
          font-size: 0.9rem;
        }

        .anomaly-details {
          display: flex;
          gap: 0.75rem;
          margin-bottom: 0.5rem;
        }

        .severity-tag {
          padding: 0.15rem 0.5rem;
          border-radius: 8px;
          font-size: 0.75rem;
          text-transform: uppercase;
          color: white;
        }

        .probability {
          color: #a8b2d1;
          font-size: 0.85rem;
        }

        .root-cause {
          color: #a8b2d1;
          font-size: 0.9rem;
          line-height: 1.4;
          margin-top: 0.5rem;
        }

        .no-anomalies {
          text-align: center;
          padding: 2rem;
          color: #4caf50;
        }

        .no-anomalies p {
          margin-top: 1rem;
          font-size: 1.1rem;
        }

        .scores-section {
          margin-top: 1.5rem;
          padding-top: 1.5rem;
          border-top: 1px solid #2a3553;
        }

        .scores-section h4 {
          margin-bottom: 1rem;
          color: #a8b2d1;
        }

        .score-row {
          display: flex;
          align-items: center;
          gap: 1rem;
          margin-bottom: 0.75rem;
        }

        .component-name {
          flex: 0 0 150px;
          font-size: 0.85rem;
          text-transform: capitalize;
        }

        .mini-score-bar {
          flex: 1;
          height: 6px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 3px;
          overflow: hidden;
        }

        .mini-fill {
          height: 100%;
          transition: width 0.5s ease;
        }

        .score-text {
          flex: 0 0 45px;
          text-align: right;
          font-size: 0.85rem;
          font-weight: 600;
        }

        .loading-container {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          min-height: 400px;
          gap: 1rem;
        }

        .spinner {
          width: 40px;
          height: 40px;
          border: 3px solid #2a3553;
          border-top-color: #00bcd4;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default PredictiveMaintenance;