// frontend/src/components/SustainabilityDashboard.jsx

import React, { useState, useEffect } from 'react';
import { Leaf, TrendingUp, Award, Target, BarChart2, Globe } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

const SustainabilityDashboard = () => {
  const [footprint, setFootprint] = useState(null);
  const [benchmarks, setBenchmarks] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const [footprintRes, benchmarksRes] = await Promise.all([
        fetch(`${API_BASE}/api/carbon/realtime`),
        fetch(`${API_BASE}/api/carbon/benchmarks`)
      ]);

      const footprintData = await footprintRes.json();
      const benchmarksData = await benchmarksRes.json();

      setFootprint(footprintData);
      setBenchmarks(benchmarksData);
      setLoading(false);
    } catch (error) {
      console.error('Error loading sustainability data:', error);
      setLoading(false);
    }
  };

  const getGradeColor = (grade) => {
    const colors = {
      'A+': '#4caf50',
      'A': '#8bc34a',
      'B+': '#cddc39',
      'B': '#ffeb3b',
      'C': '#ff9800',
      'D': '#f44336'
    };
    return colors[grade] || '#64748b';
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading sustainability metrics...</p>
      </div>
    );
  }

  return (
    <div className="sustainability-dashboard">
      <div className="dashboard-header">
        <div>
          <h1>🌱 Sustainability Dashboard</h1>
          <p>Real-time carbon footprint tracking and ESG performance</p>
        </div>
        {footprint?.sustainability_score && (
          <div className="grade-card" style={{ borderColor: getGradeColor(footprint.sustainability_score.grade) }}>
            <div className="grade-value" style={{ color: getGradeColor(footprint.sustainability_score.grade) }}>
              {footprint.sustainability_score.grade}
            </div>
            <div className="grade-label">Sustainability Grade</div>
            <div className="grade-score">{footprint.sustainability_score.total_score}/100</div>
          </div>
        )}
      </div>

      {/* Key Performance Indicators */}
      <div className="kpi-section">
        <div className="kpi-card primary">
          <div className="kpi-icon">
            <Leaf size={28} />
          </div>
          <div className="kpi-content">
            <div className="kpi-value">{footprint?.carbon_intensity_kg_co2_per_tonne?.toFixed(0) || 0}</div>
            <div className="kpi-label">kg CO₂/tonne</div>
            <div className="kpi-trend positive">
              <TrendingUp size={16} />
              <span>15% below India avg</span>
            </div>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-icon secondary">
            <BarChart2 size={28} />
          </div>
          <div className="kpi-content">
            <div className="kpi-value">{footprint?.emissions_breakdown?.total_kg_co2_per_hour?.toFixed(0) || 0}</div>
            <div className="kpi-label">kg CO₂/hour</div>
            <div className="kpi-detail">Current emissions rate</div>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-icon tertiary">
            <Globe size={28} />
          </div>
          <div className="kpi-content">
            <div className="kpi-value">{footprint?.production_rate_tonnes_per_hour?.toFixed(0) || 0}</div>
            <div className="kpi-label">tonnes/hour</div>
            <div className="kpi-detail">Production rate</div>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-icon success">
            <Award size={28} />
          </div>
          <div className="kpi-content">
            <div className="kpi-value">12,450</div>
            <div className="kpi-label">tonnes CO₂</div>
            <div className="kpi-detail">Avoided this year</div>
          </div>
        </div>
      </div>

      {/* Emissions Breakdown */}
      {footprint?.emissions_breakdown && (
        <div className="breakdown-section">
          <h2>📊 Emissions Breakdown</h2>
          <div className="breakdown-grid">
            <div className="breakdown-chart">
              <div className="pie-chart">
                {Object.entries(footprint.emissions_breakdown.breakdown_percent).map(([source, percent], idx) => (
                  <div
                    key={source}
                    className="pie-segment"
                    style={{
                      '--percent': percent,
                      '--color': ['#ff6b35', '#00bcd4', '#4caf50'][idx]
                    }}
                  >
                    <span className="segment-label">{source.replace(/_/g, ' ')}</span>
                    <span className="segment-value">{percent}%</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="breakdown-details">
              <div className="detail-card">
                <div className="detail-icon" style={{ background: '#ff6b35' }}>🔥</div>
                <div className="detail-content">
                  <div className="detail-label">Fuel Combustion</div>
                  <div className="detail-value">
                    {footprint.emissions_breakdown.fuel_combustion.toFixed(0)} kg/h
                  </div>
                  <div className="detail-percent">
                    {footprint.emissions_breakdown.breakdown_percent.fuel_combustion}% of total
                  </div>
                </div>
              </div>

              <div className="detail-card">
                <div className="detail-icon" style={{ background: '#00bcd4' }}>⚡</div>
                <div className="detail-content">
                  <div className="detail-label">Electricity</div>
                  <div className="detail-value">
                    {footprint.emissions_breakdown.electricity.toFixed(0)} kg/h
                  </div>
                  <div className="detail-percent">
                    {footprint.emissions_breakdown.breakdown_percent.electricity}% of total
                  </div>
                </div>
              </div>

              <div className="detail-card">
                <div className="detail-icon" style={{ background: '#4caf50' }}>🏭</div>
                <div className="detail-content">
                  <div className="detail-label">Process Emissions</div>
                  <div className="detail-value">
                    {footprint.emissions_breakdown.process_emissions.toFixed(0)} kg/h
                  </div>
                  <div className="detail-percent">
                    {footprint.emissions_breakdown.breakdown_percent.process_emissions}% of total
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Benchmark Comparison */}
      {footprint?.benchmark_comparison && benchmarks && (
        <div className="benchmarks-section">
          <h2>🎯 Industry Benchmarking</h2>
          <div className="benchmarks-grid">
            {Object.entries(footprint.benchmark_comparison).map(([name, data]) => (
              <div key={name} className={`benchmark-card ${data.status}`}>
                <div className="benchmark-header">
                  <span className="benchmark-name">
                    {benchmarks.benchmarks.interpretation?.[name] || name.replace(/_/g, ' ')}
                  </span>
                  <span className={`status-badge ${data.status}`}>
                    {data.status === 'better' ? '✓ Better' : '△ Higher'}
                  </span>
                </div>
                <div className="benchmark-values">
                  <div className="current-value">
                    <span className="label">Current</span>
                    <span className="value">
                      {footprint.carbon_intensity_kg_co2_per_tonne.toFixed(0)}
                    </span>
                  </div>
                  <div className="benchmark-value">
                    <span className="label">Benchmark</span>
                    <span className="value">{data.value.toFixed(0)}</span>
                  </div>
                </div>
                <div className="benchmark-diff">
                  <span className={data.status}>
                    {data.difference > 0 ? '+' : ''}{data.difference.toFixed(0)} kg
                  </span>
                  <span className="percent">
                    ({data.percentage_difference > 0 ? '+' : ''}{data.percentage_difference.toFixed(1)}%)
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Sustainability Score Breakdown */}
      {footprint?.sustainability_score?.component_scores && (
        <div className="score-breakdown-section">
          <h2>⭐ Sustainability Score Breakdown</h2>
          <div className="scores-container">
            {Object.entries(footprint.sustainability_score.component_scores).map(([component, score]) => (
              <div key={component} className="score-item">
                <div className="score-header">
                  <span className="score-name">{component.replace(/_/g, ' ')}</span>
                  <span className="score-value">{score}/100</span>
                </div>
                <div className="score-bar-container">
                  <div
                    className="score-bar-fill"
                    style={{
                      width: `${score}%`,
                      backgroundColor: score >= 80 ? '#4caf50' : score >= 60 ? '#ff9800' : '#f44336'
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
          <div className="score-interpretation">
            <p>{footprint.sustainability_score.interpretation}</p>
          </div>
        </div>
      )}

      {/* Insights */}
      {footprint?.insights && (
        <div className="insights-section">
          <h2>💡 Key Insights & Recommendations</h2>
          <div className="insights-grid">
            {footprint.insights.map((insight, idx) => (
              <div key={idx} className="insight-card">
                <div className="insight-icon">
                  {insight.includes('🌟') ? '🌟' :
                   insight.includes('⚠️') ? '⚠️' :
                   insight.includes('🔥') ? '🔥' :
                   insight.includes('🏭') ? '🏭' :
                   insight.includes('⚡') ? '⚡' : '💡'}
                </div>
                <p>{insight.replace(/[🌟⚠️🔥🏭⚡💡]/g, '').trim()}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      <style jsx>{`
        .sustainability-dashboard {
          padding: 2rem;
          max-width: 1600px;
          margin: 0 auto;
        }

        .dashboard-header {
          display: flex;
          justify-content: space-between;
          align-items: start;
          margin-bottom: 2rem;
        }

        .dashboard-header h1 {
          font-size: 2rem;
          margin-bottom: 0.5rem;
        }

        .dashboard-header p {
          color: #a8b2d1;
        }

        .grade-card {
          text-align: center;
          padding: 1.5rem 2rem;
          background: rgba(26, 34, 53, 0.7);
          border: 2px solid;
          border-radius: 12px;
          min-width: 150px;
        }

        .grade-value {
          font-size: 3rem;
          font-weight: 800;
          line-height: 1;
          margin-bottom: 0.5rem;
        }

        .grade-label {
          color: #a8b2d1;
          font-size: 0.9rem;
          margin-bottom: 0.5rem;
        }

        .grade-score {
          font-size: 1.25rem;
          font-weight: 600;
        }

        .kpi-section {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 1.5rem;
          margin-bottom: 2rem;
        }

        .kpi-card {
          display: flex;
          gap: 1.5rem;
          padding: 1.5rem;
          background: rgba(26, 34, 53, 0.7);
          border: 1px solid #2a3553;
          border-radius: 12px;
          transition: all 0.3s ease;
        }

        .kpi-card:hover {
          transform: translateY(-4px);
          box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }

        .kpi-card.primary {
          border-color: #4caf50;
        }

        .kpi-icon {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 60px;
          height: 60px;
          background: rgba(76, 175, 80, 0.1);
          border-radius: 12px;
          color: #4caf50;
        }

        .kpi-icon.secondary {
          background: rgba(0, 188, 212, 0.1);
          color: #00bcd4;
        }

        .kpi-icon.tertiary {
          background: rgba(102, 126, 234, 0.1);
          color: #667eea;
        }

        .kpi-icon.success {
          background: rgba(139, 195, 74, 0.1);
          color: #8bc34a;
        }

        .kpi-content {
          flex: 1;
        }

        .kpi-value {
          font-size: 2rem;
          font-weight: 700;
          line-height: 1;
          margin-bottom: 0.5rem;
        }

        .kpi-label {
          color: #a8b2d1;
          font-size: 0.9rem;
          margin-bottom: 0.5rem;
        }

        .kpi-trend {
          display: flex;
          align-items: center;
          gap: 0.25rem;
          font-size: 0.85rem;
        }

        .kpi-trend.positive {
          color: #4caf50;
        }

        .kpi-detail {
          color: #64748b;
          font-size: 0.85rem;
        }

        .breakdown-section,
        .benchmarks-section,
        .score-breakdown-section,
        .insights-section {
          margin-bottom: 2rem;
        }

        .breakdown-section h2,
        .benchmarks-section h2,
        .score-breakdown-section h2,
        .insights-section h2 {
          margin-bottom: 1.5rem;
          font-size: 1.5rem;
        }

        .breakdown-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 2rem;
          background: rgba(26, 34, 53, 0.7);
          border: 1px solid #2a3553;
          border-radius: 12px;
          padding: 2rem;
        }

        .breakdown-chart {
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .pie-chart {
          position: relative;
          width: 250px;
          height: 250px;
          border-radius: 50%;
          background: conic-gradient(
            #ff6b35 0% 0%,
            #00bcd4 0% 0%,
            #4caf50 0% 100%
          );
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .pie-segment {
          position: absolute;
          text-align: center;
        }

        .breakdown-details {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
        }

        .detail-card {
          display: flex;
          gap: 1rem;
          padding: 1rem;
          background: rgba(20, 27, 45, 0.5);
          border-radius: 8px;
        }

        .detail-icon {
          width: 48px;
          height: 48px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 8px;
          font-size: 1.5rem;
        }

        .detail-content {
          flex: 1;
        }

        .detail-label {
          font-weight: 600;
          margin-bottom: 0.25rem;
          text-transform: capitalize;
        }

        .detail-value {
          font-size: 1.5rem;
          font-weight: 700;
          color: #00bcd4;
        }

        .detail-percent {
          color: #64748b;
          font-size: 0.85rem;
        }

        .benchmarks-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
          gap: 1.5rem;
        }

        .benchmark-card {
          padding: 1.5rem;
          background: rgba(26, 34, 53, 0.7);
          border: 1px solid #2a3553;
          border-radius: 12px;
          transition: all 0.3s ease;
        }

        .benchmark-card:hover {
          transform: translateY(-4px);
          box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }

        .benchmark-card.better {
          border-color: #4caf50;
        }

        .benchmark-card.worse {
          border-color: #ff9800;
        }

        .benchmark-header {
          display: flex;
          justify-content: space-between;
          align-items: start;
          margin-bottom: 1rem;
        }

        .benchmark-name {
          font-weight: 600;
          font-size: 0.95rem;
          text-transform: capitalize;
        }

        .status-badge {
          padding: 0.25rem 0.75rem;
          border-radius: 12px;
          font-size: 0.75rem;
          font-weight: 600;
          text-transform: uppercase;
        }

        .status-badge.better {
          background: rgba(76, 175, 80, 0.1);
          color: #4caf50;
        }

        .status-badge.worse {
          background: rgba(255, 152, 0, 0.1);
          color: #ff9800;
        }

        .benchmark-values {
          display: flex;
          justify-content: space-between;
          margin-bottom: 1rem;
        }

        .current-value,
        .benchmark-value {
          display: flex;
          flex-direction: column;
          gap: 0.25rem;
        }

        .benchmark-values .label {
          color: #64748b;
          font-size: 0.85rem;
        }

        .benchmark-values .value {
          font-size: 1.75rem;
          font-weight: 700;
        }

        .benchmark-diff {
          display: flex;
          justify-content: space-between;
          padding-top: 1rem;
          border-top: 1px solid #2a3553;
        }

        .benchmark-diff .better {
          color: #4caf50;
          font-weight: 600;
        }

        .benchmark-diff .worse {
          color: #ff9800;
          font-weight: 600;
        }

        .benchmark-diff .percent {
          color: #64748b;
          font-size: 0.9rem;
        }

        .scores-container {
          background: rgba(26, 34, 53, 0.7);
          border: 1px solid #2a3553;
          border-radius: 12px;
          padding: 2rem;
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
        }

        .score-item {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .score-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .score-name {
          font-weight: 600;
          text-transform: capitalize;
        }

        .score-value {
          font-weight: 700;
          color: #00bcd4;
        }

        .score-bar-container {
          height: 12px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 6px;
          overflow: hidden;
        }

        .score-bar-fill {
          height: 100%;
          border-radius: 6px;
          transition: width 0.5s ease;
        }

        .score-interpretation {
          margin-top: 1rem;
          padding: 1rem;
          background: rgba(0, 188, 212, 0.1);
          border-left: 3px solid #00bcd4;
          border-radius: 4px;
          color: #a8b2d1;
          line-height: 1.6;
        }

        .insights-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
          gap: 1.5rem;
        }

        .insight-card {
          display: flex;
          gap: 1rem;
          padding: 1.5rem;
          background: rgba(26, 34, 53, 0.7);
          border: 1px solid #2a3553;
          border-left: 3px solid #00bcd4;
          border-radius: 12px;
          transition: all 0.3s ease;
        }

        .insight-card:hover {
          transform: translateX(4px);
          box-shadow: 0 5px 20px rgba(0, 0, 0, 0.2);
        }

        .insight-icon {
          font-size: 2rem;
          flex-shrink: 0;
        }

        .insight-card p {
          line-height: 1.6;
          color: #a8b2d1;
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

        @media (max-width: 1024px) {
          .breakdown-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
};

export default SustainabilityDashboard;