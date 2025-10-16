from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
import asyncio
import json
from datetime import datetime, timedelta
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.database import Base, engine, get_db, SensorReading, AgentCommunication, AsyncSessionLocal
from app.models.sensors import SensorData, UnitStatus, AnomalyAlert
from app.models.agents import AnalyticsQuery, AnalyticsResponse, AgentState
from app.services.data_simulator import simulator
from app.services.ai_agents import agent_orchestrator

# ===== ADD THIS IMPORT =====
from app.api.enhanced_endpoints import router as enhanced_router

# ===== CREATE APP FIRST =====
app = FastAPI(title="Cement AI Optimizer", version="1.0.0")

# ===== THEN ADD CORS MIDDLEWARE =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== THEN INCLUDE THE ENHANCED ROUTER =====
app.include_router(enhanced_router, tags=["Enhanced Features"])


# WebSocket connections manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass


manager = ConnectionManager()

# Background tasks
background_tasks = set()


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database and start background tasks"""
    print("🚀 Starting Cement AI Optimizer...")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database initialized")

    # Start data simulation
    task1 = asyncio.create_task(simulator.simulate_continuous_data())
    background_tasks.add(task1)
    print("✅ Data simulator started")

    # Start sensor data broadcast
    task2 = asyncio.create_task(broadcast_sensor_data())
    background_tasks.add(task2)
    print("✅ Sensor broadcast started")


# Replace the broadcast_sensor_data function in your main.py with this fixed version

async def broadcast_sensor_data():
    """Broadcast sensor data to all connected clients"""
    while True:
        try:
            # Get latest sensor readings
            async with AsyncSessionLocal() as session:
                # Get readings from last 5 seconds
                cutoff_time = datetime.utcnow() - timedelta(seconds=5)
                result = await session.execute(
                    select(SensorReading).where(SensorReading.timestamp >= cutoff_time)
                )
                readings = result.scalars().all()

                if readings:
                    # Group by unit
                    units_data = {}
                    for reading in readings:
                        if reading.unit not in units_data:
                            units_data[reading.unit] = []

                        sensor_data = SensorData(
                            unit=reading.unit,
                            sensor_name=reading.sensor_name,
                            value=reading.value,
                            unit_measure=reading.unit_measure,
                            timestamp=reading.timestamp,
                            is_anomaly=reading.is_anomaly
                        )
                        units_data[reading.unit].append(sensor_data)

                    # Process through AI agents and detect anomalies
                    anomalies = []
                    for unit, data in units_data.items():
                        try:
                            # Use process_sensor_data instead of process_with_public_data
                            analysis = await agent_orchestrator.process_sensor_data(unit, data)

                            # Check for anomalies
                            unit_anomalies = simulator.detect_anomalies(data)
                            if unit_anomalies:
                                anomalies.extend(unit_anomalies)
                                # Handle through agents
                                await agent_orchestrator.handle_anomalies(unit_anomalies)
                        except Exception as e:
                            print(f"⚠️ Error processing unit {unit}: {e}")
                            continue

                    # Broadcast to WebSocket clients
                    await manager.broadcast({
                        "type": "sensor_update",
                        "timestamp": datetime.utcnow().isoformat(),
                        "data": {
                            unit: [s.dict() for s in sensors]
                            for unit, sensors in units_data.items()
                        },
                        "anomalies": [a.dict() for a in anomalies] if anomalies else []
                    })

            await asyncio.sleep(settings.SIMULATION_INTERVAL)

        except Exception as e:
            print(f"❌ Error in broadcast task: {e}")
            await asyncio.sleep(settings.SIMULATION_INTERVAL)


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Enhanced WebSocket endpoint with public data updates"""
    await manager.connect(websocket)
    print(f"🔌 New WebSocket connection. Total connections: {len(manager.active_connections)}")

    try:
        # Send initial data
        plant_config = settings.PLANT_CONFIGS[0] if settings.PLANT_CONFIGS else {}
        if plant_config:
            public_data = await public_data_service.aggregate_public_data(plant_config)
            await websocket.send_json({
                "type": "initial_data",
                "public_data_available": bool(public_data),
                "plant_config": plant_config
            })

        while True:
            # Keep connection alive and wait for messages
            data = await websocket.receive_text()
            # Echo back to confirm connection is alive
            await websocket.send_json({"type": "ping", "status": "connected"})

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"🔌 WebSocket disconnected. Remaining connections: {len(manager.active_connections)}")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        manager.disconnect(websocket)


# Health check
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "services": {
            "database": "connected",
            "gemini_ai": "active",
            "public_data": "available" if settings.USE_PUBLIC_DATA else "disabled",
            "simulation": "running",
            "websocket_connections": len(manager.active_connections)
        }
    }


# Units Status
@app.get("/api/units/status")
async def get_units_status():
    """Get current status of all production units"""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(SensorReading)
                .order_by(SensorReading.timestamp.desc())
                .limit(100)
            )
            readings = result.scalars().all()

            units_status = {}
            for reading in readings:
                if reading.unit not in units_status:
                    units_status[reading.unit] = {
                        "unit": reading.unit,
                        "health_score": 85,
                        "efficiency": 87.5,
                        "status": "normal",
                        "sensors": []
                    }

                units_status[reading.unit]["sensors"].append({
                    "name": reading.sensor_name,
                    "value": reading.value,
                    "unit": reading.unit_measure,
                    "is_anomaly": reading.is_anomaly
                })

            return list(units_status.values())
    except Exception as e:
        print(f"Error in get_units_status: {e}")
        return []


# Agent States
@app.get("/api/agents/states")
async def get_agent_states():
    """Get current state of all AI agents"""
    try:
        states = await agent_orchestrator.get_all_agent_states()
        return states
    except Exception as e:
        print(f"Error in get_agent_states: {e}")
        return {}


# Agent Communications
@app.get("/api/agents/communications")
async def get_agent_communications(limit: int = 50):
    """Get recent agent communications"""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(AgentCommunication)
                .order_by(AgentCommunication.timestamp.desc())
                .limit(limit)
            )
            communications = result.scalars().all()

            return [
                {
                    "id": comm.id,
                    "from_agent": comm.from_agent,
                    "to_agent": comm.to_agent,
                    "message_type": comm.message_type,
                    "severity": comm.severity,
                    "message": comm.message,
                    "timestamp": comm.timestamp.isoformat()
                }
                for comm in communications
            ]
    except Exception as e:
        print(f"Error in get_agent_communications: {e}")
        return []


# ✅ FIXED: Analytics Query Endpoint - THIS WAS MISSING!
@app.post("/api/analytics/query")
async def analytics_query(query: AnalyticsQuery):
    """
    Answer user queries using AI agents with context
    THIS ENDPOINT WAS MISSING AND IS NOW FIXED!
    """
    try:
        print(f"📊 Processing analytics query: {query.question}")

        # Use the agent orchestrator to answer the query
        response = await agent_orchestrator.answer_query(query.question)

        return {
            "query": query.question,
            "responding_agent": response.get("responding_agent", "AI Agent"),
            "answer": response.get("answer", "I apologize, but I couldn't process your query at this time."),
            "confidence": response.get("confidence", 0.7),
            "sources": response.get("sources", ["Gemini AI Model"]),
            "data_sources_used": response.get("data_sources_used", []),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        print(f"❌ Error in analytics query: {e}")
        import traceback
        traceback.print_exc()

        return {
            "query": query.question,
            "responding_agent": "Error Handler",
            "answer": f"I encountered an error processing your query: {str(e)}. Please try again or rephrase your question.",
            "confidence": 0.0,
            "sources": [],
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


# Sensors Endpoints
@app.get("/api/sensors/latest/{unit}")
async def get_latest_sensors(unit: str):
    """Get latest sensor readings for a unit"""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(SensorReading)
                .where(SensorReading.unit == unit)
                .order_by(SensorReading.timestamp.desc())
                .limit(50)
            )
            readings = result.scalars().all()

            return [
                {
                    "sensor_name": r.sensor_name,
                    "value": r.value,
                    "unit_measure": r.unit_measure,
                    "is_anomaly": r.is_anomaly,
                    "timestamp": r.timestamp.isoformat()
                }
                for r in readings
            ]
    except Exception as e:
        print(f"Error in get_latest_sensors: {e}")
        return []


@app.get("/api/sensors/historical/{unit}")
async def get_historical_sensors(unit: str, hours: int = 24):
    """Get historical sensor data"""
    try:
        start_time = datetime.utcnow() - timedelta(hours=hours)

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(SensorReading)
                .where(and_(
                    SensorReading.unit == unit,
                    SensorReading.timestamp >= start_time
                ))
                .order_by(SensorReading.timestamp.desc())
            )
            readings = result.scalars().all()

            return [
                {
                    "sensor_name": r.sensor_name,
                    "value": r.value,
                    "unit_measure": r.unit_measure,
                    "is_anomaly": r.is_anomaly,
                    "timestamp": r.timestamp.isoformat()
                }
                for r in readings
            ]
    except Exception as e:
        print(f"Error in get_historical_sensors: {e}")
        return []


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)