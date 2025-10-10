const API_BASE_URL = 'http://localhost:8000/api';

// Helper function for API calls
const apiCall = async (endpoint, options = {}) => {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API call failed: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`Error calling ${endpoint}:`, error);
    throw error;
  }
};

// Units Status
export const getUnitsStatus = () => apiCall('/units/status');

export const getLatestSensorData = (unit) => apiCall(`/sensors/latest/${unit}`);

export const getHistoricalData = (unit, hours = 24) =>
  apiCall(`/sensors/historical/${unit}?hours=${hours}`);

// Agents
export const getAgentStates = () => apiCall('/agents/states');

export const getAgentCommunications = (limit = 50) =>
  apiCall(`/agents/communications?limit=${limit}`);

// Analytics
export const queryAnalytics = async (question, context = null, includeHistorical = false) => {
  return apiCall('/analytics/query', {
    method: 'POST',
    body: JSON.stringify({
      question,
      context,
      include_historical: includeHistorical,
    }),
  });
};

// Public Data
export const getPublicData = () => apiCall('/public-data/latest');

// Optimization
export const optimizeFuelMix = async (constraints = {}) => {
  return apiCall('/optimization/fuel-mix', {
    method: 'POST',
    body: JSON.stringify(constraints),
  });
};

export const optimizeWithPublicData = () => apiCall('/optimization/with-public-data');

export const comprehensiveOptimization = () =>
  apiCall('/optimization/comprehensive', { method: 'POST' });

// Chemistry Validation
export const validateChemistry = (composition) => {
  const params = new URLSearchParams(composition);
  return apiCall(`/chemistry/validate?${params}`);
};

export default {
  getUnitsStatus,
  getLatestSensorData,
  getHistoricalData,
  getAgentStates,
  getAgentCommunications,
  queryAnalytics,
  getPublicData,
  optimizeFuelMix,
  optimizeWithPublicData,
  comprehensiveOptimization,
  validateChemistry,
};