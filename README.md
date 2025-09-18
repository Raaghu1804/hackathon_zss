# Cement AI Optimizer - Intelligent Plant Operations Platform

## Overview

An AI-driven cement plant optimization platform that leverages Generative AI to optimize energy consumption, quality control, and sustainability across cement production processes. The system features autonomous AI agents for Pre-Calciner, Rotary Kiln, and Clinker Cooler units that communicate and coordinate to maintain optimal operations.

## Key Features

### 🤖 AI Agent Architecture

* **Three Autonomous AI Agents** :
* Pre-Calciner Agent: Manages temperature, calcination degree, and fuel optimization
* Rotary Kiln Agent: Controls burning zone temperature, shell monitoring, and clinker quality
* Clinker Cooler Agent: Optimizes cooling efficiency, air flow, and heat recovery

### 📊 Real-time Monitoring

* Live sensor data simulation with 5-second update frequency
* Comprehensive dashboards for each production unit
* Anomaly detection and automatic response system
* WebSocket-based real-time data streaming

### 💬 Inter-Agent Communication

* Agents communicate to resolve cross-unit issues
* Coordinated optimization strategies
* Severity-based alert system
* Complete communication audit trail

### 🔍 AI Analytics

* Natural language query interface
* Context-aware responses from appropriate agents
* Process optimization recommendations
* Historical data analysis

## System Architecture

### Technology Stack

* **Backend** : FastAPI (Python 3.9+)
* **Frontend** : React 18
* **Database** : SQLite with SQLAlchemy ORM
* **AI Integration** : Google Gemini API
* **Real-time Communication** : WebSockets
* **Data Simulation** : NumPy-based sensor simulation

### Sensor Parameters Monitored

#### Pre-Calciner

* Temperature: 820-900°C
* Pressure: -5 to -2 mbar
* Oxygen Level: 2-4%
* CO Level: 0-0.1%
* NOx Level: 0-800 mg/Nm³
* Fuel Flow: 8-12 t/h
* Feed Rate: 250-350 t/h
* Tertiary Air Temperature: 600-900°C
* Calcination Degree: 85-95%

#### Rotary Kiln

* Burning Zone Temperature: 1400-1500°C
* Back End Temperature: 800-1200°C
* Shell Temperature: 200-350°C
* Oxygen Level: 1-3%
* NOx Level: 0-1200 mg/Nm³
* CO Level: 0-0.05%
* Kiln Speed: 3-5 rpm
* Fuel Rate: 10-15 t/h
* Clinker Exit Temperature: 1100-1300°C

#### Clinker Cooler

* Inlet Temperature: 1100-1300°C
* Outlet Temperature: 100-150°C
* Secondary Air Temperature: 600-1000°C
* Tertiary Air Temperature: 600-900°C
* Grate Speed: 10-30 strokes/min
* Undergrate Pressure: 40-80 mbar
* Cooling Air Flow: 2.3-3.3 kg/kg
* Bed Height: 500-800 mm
* Cooler Efficiency: 75-85%

## Installation & Setup

### Prerequisites

* Python 3.9 or higher
* Node.js 16 or higher
* Git

### Backend Setup

1. Clone the repository:

```bash
git clone https://github.com/yourcompany/cement-ai-optimizer.git
cd cement-ai-optimizer
```

2. Create a Python virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install backend dependencies:

```bash
cd backend
pip install -r requirements.txt
```

4. Create a `.env` file in the backend directory:

```env
GEMINI_API_KEY=AIzaSyBvIzIMpPcqUduNF6rSUL2o-ClYWO4GtTA
DATABASE_URL=sqlite+aiosqlite:///./cement_plant.db
```

5. Run the backend server:

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

1. Open a new terminal and navigate to the frontend directory:

```bash
cd frontend
```

2. Install dependencies:

```bash
npm install
```

3. Start the development server:

```bash
npm start
```

The application will open at `http://localhost:3000`

## Usage Guide

### Dashboard

* View real-time status of all three production units
* Monitor key performance indicators (KPIs)
* Track plant efficiency, energy consumption, and production rate
* Visual indicators for unit health and efficiency scores

### Agent Communications

* View real-time communication between AI agents
* Filter by severity levels (info, warning, critical)
* Track coordinated responses to anomalies
* Review action history

### AI Analytics

* Ask questions in natural language about plant operations
* Example queries:
  * "What is the current efficiency of the pre-calciner?"
  * "How can we optimize the rotary kiln temperature?"
  * "What are the main issues in the clinker cooler?"
* Receive AI-powered insights and recommendations

## API Documentation

### Core Endpoints

#### GET `/api/units/status`

Returns current status of all production units including health scores and efficiency metrics.

#### GET `/api/sensors/latest/{unit}`

Retrieves the latest sensor readings for a specific unit (precalciner, rotary_kiln, clinker_cooler).

#### GET `/api/sensors/historical/{unit}`

Returns historical sensor data for trend analysis and charts.

#### GET `/api/agents/states`

Provides current operational state of all AI agents.

#### GET `/api/agents/communications`

Returns recent inter-agent communications with severity levels and actions taken.

#### POST `/api/analytics/query`

Submit natural language queries for AI analysis.

Request body:

```json
{
  "question": "Your question here",
  "context": "optional context",
  "include_historical": false
}
```

#### WebSocket `/ws`

Real-time sensor data stream with automatic updates every 5 seconds.

## Development

### Project Structure

```
cement-ai-optimizer/
├── backend/
│   ├── app/
│   │   ├── models/         # Data models
│   │   ├── services/       # Business logic
│   │   ├── api/           # API routes
│   │   └── main.py        # Application entry
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── services/      # API services
│   │   └── App.jsx        # Main application
└── README.md
```

### Adding New Sensors

1. Update sensor ranges in `backend/app/config.py`
2. Modify the data simulator in `backend/app/services/data_simulator.py`
3. Update the frontend display components

### Customizing AI Agents

1. Extend the base `CementPlantAgent` class in `backend/app/services/ai_agents.py`
2. Implement unit-specific anomaly handling
3. Define communication protocols with other agents

## Performance Optimization

* **Database** : Indexes on timestamp and unit fields for faster queries
* **WebSocket** : Efficient broadcasting to multiple clients
* **Data Simulation** : Optimized numpy operations for sensor value generation
* **Frontend** : React memo and useMemo for expensive computations

## Security Considerations

* API key management through environment variables
* CORS configuration for frontend access
* Input validation on all endpoints
* Rate limiting on analytics queries (recommended for production)

## Troubleshooting

### Common Issues

1. **WebSocket connection fails**
   * Ensure backend is running on port 8000
   * Check CORS settings in backend config
2. **No sensor data appearing**
   * Verify data simulator is running (check backend logs)
   * Confirm database tables are created
3. **AI Analytics not responding**
   * Check Gemini API key validity
   * Review API quota limits

## Future Enhancements

* [ ] Integration with real plant sensors via OPC UA
* [ ] Machine learning models for predictive maintenance
* [ ] Mobile application for remote monitoring
* [ ] Advanced visualization with 3D plant models
* [ ] Multi-plant management dashboard
* [ ] Integration with ERP systems
* [ ] Carbon footprint tracking and optimization
* [ ] Alternative fuel optimization algorithms

## Support

For technical support or questions, please contact the development team.

## License

Proprietary software - All rights reserved.

## Acknowledgments

Built with modern web technologies and powered by Google Gemini AI for intelligent decision-making in cement manufacturing operations.
