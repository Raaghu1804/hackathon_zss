// frontend/src/components/FuelOptimizer.jsx

import React, { useState, useEffect } from 'react';
import { Fuel, TrendingDown, DollarSign, Leaf, Sliders, BarChart3, RefreshCw } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

const FuelOptimizer = () => {
  const [optimization, setOptimization] = useState(null);
  const [savings, setSavings] = useState(null);
  const [loading, setLoading] = useState(false);

  // Optimization parameters
  const [energyRequired, setEnergyRequired] = useState(10000);
  const [costPriority, setCostPriority] = useState(0.5);
  const [maxAFR, setMaxAFR] = useState(0.65);

  useEffect(() => {
    optimizeFuelMix();
  }, []);

  const optimizeFuelMix = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `${API_BASE}/api/fuel/optimize?total_energy_gj=${energyRequired}&cost_priority=${costPriority}&max_afr=${maxAFR}`
      );
      const data = await response.json();
      setOptimization(data);

      // Get savings
      const savingsResponse = await fetch(`${API_BASE}/api/fuel/savings`);
      const savingsData = await savingsResponse.json();
      setSavings(savingsData);
    } catch (error) {
      console.error('Error optimizing fuel mix:', error);
    }
    setLoading(false);
  };

  const getFuelColor = (fuel) => {
    const colors = {
      coal: '#424242',
      rice_husk: '#8bc34a',
      rdf: '#ff9800',
      biomass: '#4caf50',
      petcoke: '#9e9e9e',
      plastic_waste: '#2196f3'
    };
    return colors[fuel] || '#64748b';
  };

  const getFuelIcon = (fuel) => {
    return '🔥';
  };

  if (loading && !optimization) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Optimizing fuel mix...</p>
      </div>
    );
  }

  return (
    <div className="fuel-optimizer">
      <div className="optimizer-header">
        <div>
          <h1>⚡ Alternative Fuel Optimizer</h1>
          <p>AI-powered fuel mix optimization for cost and sustainability</p>
        </div>
        <button className="refresh-btn" onClick={optimizeFuelMix} disabled={loading}>
          <RefreshCw size={20} className={loading ? 'spinning' : ''} />
          {loading ? 'Optimizing...' : 'Refresh'}
        </button>
      </div>

      {/* Control Panel */}
      <div className="control-panel">
        <h2>Optimization Parameters</h2>
        <div className="controls-grid">
          <div className="control-item">
            <label>
              <Sliders size={16} />
              Energy Required (GJ)
            </label>
            <input
              type="number"
              value={energyRequired}
              onChange={(e) => setEnergyRequired(Number(e.target.value))}
              min="1000"
              max="50000"
              step="1000"
            />
            <span className="help-text">Total thermal energy requirement</span>
          </div>

          <div className="control-item">
            <label>
              <BarChart3 size={16} />
              Cost Priority: {(costPriority * 100).toFixed(0)}%
            </label>
            <input
              type="range"
              value={costPriority}
              onChange={(e) => setCostPriority(Number(e.target.value))}
              min="0"
              max="1"
              step="0.1"
            />
            <div className="range-labels">
              <span>Emissions Focus</span>
              <span>Cost Focus</span>
            </div>
          </div>

          <div className="control-item">
            <label>
              <Fuel size={16} />
              Max AFR: {(maxAFR * 100).toFixed(0)}%
            </label>
            <input
              type="range"
              value={maxAFR}
              onChange={(e) => setMaxAFR(Number(e.target.value))}
              min="0.3"
              max="0.8"
              step="0.05"
            />
            <span className="help-text">Maximum alternative fuel rate</span>
          </div>

          <button className="optimize-btn" onClick={optimizeFuelMix} disabled={loading}>
            Optimize Mix
          </button>
        </div>
      </div>

      {optimization && optimization.success && (
        <>
          {/* Key Metrics */}
          <div className="metrics-section">
            <div className="metric-card primary">
              <div className="metric-icon" style={{ backgroundColor: '#00bcd4' }}>
                <Fuel size={24} />
              </div>
              <div className="metric-content">
                <div className="metric-value">{optimization.alternative_fuel_rate_percent}%</div>
                <div className="metric-label">Alternative Fuel Rate</div>
              </div>
            </div>

            <div className="metric-card success">
              <div className="metric-icon" style={{ backgroundColor: '#4caf50' }}>
                <DollarSign size={24} />
              </div>
              <div className="metric-content">
                <div className="metric-value">${(optimization.economics.cost_savings_usd / 1000).toFixed(1)}K</div>
                <div className="metric-label">Cost Savings</div>
                <div className="metric-sub">({optimization.economics.cost_savings_percent}% reduction)</div>
              </div>
            </div>

            <div className="metric-card eco">
              <div className="metric-icon" style={{ backgroundColor: '#8bc34a' }}>
                <Leaf size={24} />
              </div>
              <div className="metric-content">
                <div className="metric-value">{optimization.environmental.co2_reduction_tonnes}t</div>
                <div className="metric-label">CO₂ Reduction</div>
                <div className="metric-sub">({optimization.environmental.co2_reduction_percent}% lower)</div>
              </div>
            </div>

            <div className="metric-card warning">
              <div className="metric-icon" style={{ backgroundColor: '#ff9800' }}>
                <TrendingDown size={24} />
              </div>
              <div className="metric-content">
                <div className="metric-value">{optimization.quality_metrics.weighted_ash_content.toFixed(1)}%</div>
                <div className="metric-label">Ash Content</div>
                <div className="metric-sub">{optimization.quality_metrics.weighted_calorific_value.toFixed(1)} MJ/kg</div>
              </div>
            </div>
          </div>

          {/* Fuel Mix Visualization */}
          <div className="fuel-mix-section">
            <h2>🎯 Optimized Fuel Mix</h2>
            <div className="fuel-mix-container">
              <div className="fuel-breakdown">
                {Object.entries(optimization.optimal_mix).map(([fuel, fraction]) => (
                  <div key={fuel} className="fuel-item">
                    <div className="fuel-header">
                      <div className="fuel-name">
                        <span className="fuel-icon">{getFuelIcon(fuel)}</span>
                        <span>{fuel.replace(/_/g, ' ').toUpperCase()}</span>
                      </div>
                      <span className="fuel-percent">{(fraction * 100).toFixed(1)}%</span>
                    </div>
                    <div className="fuel-bar">
                      <div
                        className="fuel-fill"
                        style={{
                          width: `${fraction * 100}%`,
                          backgroundColor: getFuelColor(fuel)
                        }}
                      />
                    </div>
                    <div className="fuel-energy">
                      {optimization.energy_breakdown_gj[fuel].toFixed(0)} GJ
                    </div>
                  </div>
                ))}
              </div>

              <div className="comparison-chart">
                <h3>Cost & Emissions Comparison</h3>
                <div className="comparison-bars">
                  <div className="comparison-item">
                    <div className="comparison-label">Cost</div>
                    <div className="comparison-row">
                      <span className="row-label">Baseline</span>
                      <div className="bar-container">
                        <div
                          className="bar baseline"
                          style={{ width: '100%' }}
                        />
                        <span className="bar-value">${optimization.economics.total_cost_usd.toLocaleString()}</span>
                      </div>
                    </div>
                  </div>

                  <div className="comparison-item">
                    <div className="comparison-label">CO₂ Emissions</div>
                    <div className="comparison-row">
                      <span className="row-label">Baseline</span>
                      <div className="bar-container">
                        <div
                          className="bar baseline"
                          style={{ width: '100%' }}
                        />
                        <span className="bar-value">{optimization.environmental.baseline_co2_tonnes}t</span>
                      </div>
                    </div>
                    <div className="comparison-row">
                      <span className="row-label">Optimized</span>
                      <div className="bar-container">
                        <div
                          className="bar optimized eco"
                          style={{
                            width: `${(optimization.environmental.total_co2_tonnes / optimization.environmental.baseline_co2_tonnes) * 100}%`
                          }}
                        />
                        <span className="bar-value">{optimization.environmental.total_co2_tonnes}t</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Recommendations */}
          {optimization.recommendations && optimization.recommendations.length > 0 && (
            <div className="recommendations-section">
              <h2>💡 AI Recommendations</h2>
              <div className="recommendations-grid">
                {optimization.recommendations.map((rec, idx) => (
                  <div key={idx} className="recommendation-card">
                    <div className="rec-number">{idx + 1}</div>
                    <p>{rec}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Savings Projection */}
          {savings && (
            <div className="savings-section">
              <h2>💰 Savings Projection</h2>
              <div className="savings-grid">
                <div className="savings-card">
                  <div className="period">Monthly</div>
                  <div className="savings-amount">${savings.savings.monthly_savings_usd.toLocaleString()}</div>
                  <div className="savings-detail">
                    <Leaf size={16} />
                    <span>{savings.savings.monthly_co2_reduction_tonnes}t CO₂ reduced</span>
                  </div>
                </div>

                <div className="savings-card highlight">
                  <div className="period">Annual</div>
                  <div className="savings-amount">${savings.savings.annual_savings_usd.toLocaleString()}</div>
                  <div className="savings-detail">
                    <Leaf size={16} />
                    <span>{savings.savings.annual_co2_reduction_tonnes}t CO₂ reduced</span>
                  </div>
                </div>

                <div className="savings-card">
                  <div className="period">ROI</div>
                  <div className="savings-amount">{savings.savings.roi_months} months</div>
                  <div className="savings-detail">
                    <TrendingDown size={16} />
                    <span>Payback period</span>
                  </div>
                </div>

                <div className="savings-card info">
                  <div className="period">Current AFR</div>
                  <div className="savings-amount">{savings.alternative_fuel_rate.toFixed(1)}%</div>
                  <div className="savings-detail">
                    <Fuel size={16} />
                    <span>Alternative fuels</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      <style jsx>{`
        .fuel-optimizer {
          padding: 2rem;
          max-width: 1600px;
          margin: 0 auto;
        }

        .optimizer-header {
          display: flex;
          justify-content: space-between;
          align-items: start;
          margin-bottom: 2rem;
        }

        .optimizer-header h1 {
          font-size: 2rem;
          margin-bottom: 0.5rem;
        }

        .optimizer-header p {
          color: #a8b2d1;
        }

        .refresh-btn {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.75rem 1.5rem;
          background: linear-gradient(135deg, #00bcd4 0%, #0097a7 100%);
          border: none;
          border-radius: 8px;
          color: white;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .refresh-btn:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 5px 15px rgba(0, 188, 212, 0.3);
        }

        .refresh-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .spinning {
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .control-panel {
          background: rgba(26, 34, 53, 0.7);
          border: 1px solid #2a3553;
          border-radius: 12px;
          padding: 2rem;
          margin-bottom: 2rem;
        }

        .control-panel h2 {
          margin-bottom: 1.5rem;
          font-size: 1.25rem;
        }

        .controls-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
          gap: 2rem;
        }

        .control-item {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }

        .control-item label {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-weight: 600;
          color: #e0e6ed;
        }

        .control-item input[type="number"] {
          padding: 0.75rem;
          background: rgba(20, 27, 45, 0.5);
          border: 1px solid #2a3553;
          border-radius: 8px;
          color: #e0e6ed;
          font-size: 1rem;
        }

        .control-item input[type="range"] {
          width: 100%;
          height: 6px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 3px;
          outline: none;
        }

        .control-item input[type="range"]::-webkit-slider-thumb {
          appearance: none;
          width: 18px;
          height: 18px;
          background: #00bcd4;
          border-radius: 50%;
          cursor: pointer;
        }

        .range-labels {
          display: flex;
          justify-content: space-between;
          font-size: 0.85rem;
          color: #a8b2d1;
        }

        .help-text {
          font-size: 0.85rem;
          color: #64748b;
        }

        .optimize-btn {
          padding: 1rem 2rem;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          border: none;
          border-radius: 8px;
          color: white;
          font-weight: 600;
          font-size: 1rem;
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .optimize-btn:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }

        .metrics-section {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 1.5rem;
          margin-bottom: 2rem;
        }

        .metric-card {
          display: flex;
          align-items: center;
          gap: 1.5rem;
          padding: 1.5rem;
          background: rgba(26, 34, 53, 0.7);
          border: 1px solid #2a3553;
          border-radius: 12px;
          transition: all 0.3s ease;
        }

        .metric-card:hover {
          transform: translateY(-4px);
          box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }

        .metric-icon {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 60px;
          height: 60px;
          border-radius: 12px;
          color: white;
        }

        .metric-content {
          flex: 1;
        }

        .metric-value {
          font-size: 1.75rem;
          font-weight: 700;
          margin-bottom: 0.25rem;
        }

        .metric-label {
          color: #a8b2d1;
          font-size: 0.9rem;
        }

        .metric-sub {
          color: #64748b;
          font-size: 0.85rem;
          margin-top: 0.25rem;
        }

        .fuel-mix-section {
          margin-bottom: 2rem;
        }

        .fuel-mix-section h2 {
          margin-bottom: 1.5rem;
          font-size: 1.5rem;
        }

        .fuel-mix-container {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 2rem;
        }

        .fuel-breakdown {
          background: rgba(26, 34, 53, 0.7);
          border: 1px solid #2a3553;
          border-radius: 12px;
          padding: 2rem;
        }

        .fuel-item {
          margin-bottom: 1.5rem;
        }

        .fuel-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 0.5rem;
        }

        .fuel-name {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-weight: 600;
        }

        .fuel-icon {
          font-size: 1.25rem;
        }

        .fuel-percent {
          font-size: 1.25rem;
          font-weight: 700;
          color: #00bcd4;
        }

        .fuel-bar {
          height: 12px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 6px;
          overflow: hidden;
          margin-bottom: 0.5rem;
        }

        .fuel-fill {
          height: 100%;
          border-radius: 6px;
          transition: width 0.5s ease;
        }

        .fuel-energy {
          color: #a8b2d1;
          font-size: 0.9rem;
        }

        .comparison-chart {
          background: rgba(26, 34, 53, 0.7);
          border: 1px solid #2a3553;
          border-radius: 12px;
          padding: 2rem;
        }

        .comparison-chart h3 {
          margin-bottom: 1.5rem;
          color: #a8b2d1;
        }

        .comparison-bars {
          display: flex;
          flex-direction: column;
          gap: 2rem;
        }

        .comparison-item {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .comparison-label {
          font-weight: 600;
          font-size: 1.1rem;
        }

        .comparison-row {
          display: grid;
          grid-template-columns: 80px 1fr;
          align-items: center;
          gap: 1rem;
        }

        .row-label {
          color: #a8b2d1;
          font-size: 0.9rem;
        }

        .bar-container {
          position: relative;
          display: flex;
          align-items: center;
          gap: 1rem;
        }

        .bar {
          height: 32px;
          border-radius: 6px;
          transition: width 0.5s ease;
        }

        .bar.baseline {
          background: linear-gradient(90deg, #64748b, #94a3b8);
        }

        .bar.optimized {
          background: linear-gradient(90deg, #00bcd4, #0097a7);
        }

        .bar.optimized.eco {
          background: linear-gradient(90deg, #4caf50, #8bc34a);
        }

        .bar-value {
          font-weight: 600;
          font-size: 0.9rem;
          white-space: nowrap;
        }

        .recommendations-section {
          margin-bottom: 2rem;
        }

        .recommendations-section h2 {
          margin-bottom: 1.5rem;
          font-size: 1.5rem;
        }

        .recommendations-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
          gap: 1.5rem;
        }

        .recommendation-card {
          display: flex;
          gap: 1rem;
          padding: 1.5rem;
          background: rgba(26, 34, 53, 0.7);
          border: 1px solid #2a3553;
          border-left: 3px solid #00bcd4;
          border-radius: 12px;
        }

        .rec-number {
          flex-shrink: 0;
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: rgba(0, 188, 212, 0.2);
          border-radius: 50%;
          color: #00bcd4;
          font-weight: 700;
        }

        .recommendation-card p {
          line-height: 1.6;
          color: #a8b2d1;
        }

        .savings-section {
          margin-bottom: 2rem;
        }

        .savings-section h2 {
          margin-bottom: 1.5rem;
          font-size: 1.5rem;
        }

        .savings-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 1.5rem;
        }

        .savings-card {
          padding: 2rem;
          background: rgba(26, 34, 53, 0.7);
          border: 1px solid #2a3553;
          border-radius: 12px;
          text-align: center;
          transition: all 0.3s ease;
        }

        .savings-card:hover {
          transform: translateY(-4px);
          box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }

        .savings-card.highlight {
          border-color: #00bcd4;
          background: rgba(0, 188, 212, 0.1);
        }

        .period {
          color: #a8b2d1;
          font-size: 0.9rem;
          margin-bottom: 0.5rem;
          text-transform: uppercase;
        }

        .savings-amount {
          font-size: 2rem;
          font-weight: 700;
          margin-bottom: 1rem;
        }

        .savings-detail {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.5rem;
          color: #64748b;
          font-size: 0.9rem;
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

        @media (max-width: 1024px) {
          .fuel-mix-container {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
};

export default FuelOptimizer;