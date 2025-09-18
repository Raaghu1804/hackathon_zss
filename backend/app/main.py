# backend/app/main.py

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
import asyncio
import json
from datetime import datetime, timedelta
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.database import Base, engine, get_db, SensorReading, AgentCommunication
from app.models.sensors import SensorData, UnitStatus, AnomalyAlert
from app.models.agents import AnalyticsQuery, AnalyticsResponse, AgentState
from app.services.data_simulator import simulator
from app.services.ai_agents import agent_orchestrator

app = FastAPI(title="Cement AI Optimizer", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database and start simulation"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Start data simulation
    asyncio.create_task(simulator.simulate_continuous_data())
    asyncio.create_task(broadcast_sensor_data())

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Stop simulation on shutdown"""
    simulator.stop_simulation()

# Background task to broadcast sensor data
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
                        analysis = await agent_orchestrator.process_sensor_data(unit, data)
                        
                        # Check for anomalies
                        unit_anomalies = simulator.detect_anomalies(data)
                        if unit_anomalies:
                            anomalies.extend(unit_anomalies)
                            # Handle through agents
                            await agent_orchestrator.handle_anomalies(unit_anomalies)
                    
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
            print(f"Error in broadcast task: {e}")
            await asyncio.sleep(settings.SIMULATION_INTERVAL)

# API Endpoints

@app.get("/")
async def root():
    return {"message": "Cement AI Optimizer API", "status": "running"}

@app.get("/api/units/status")
async def get_units_status(db: AsyncSession = Depends(get_db)):
    """Get current status of all units"""
    units = ["precalciner", "rotary_kiln", "clinker_cooler"]
    statuses = []
    
    for unit in units:
        # Get latest readings for unit
        result = await db.execute(
            select(SensorReading).where(SensorReading.unit == unit).order_by(
                SensorReading.timestamp.desc()
            ).limit(20)
        )
        readings = result.scalars().all()
        
        if readings:
            # Calculate health and efficiency
            anomaly_count = sum(1 for r in readings if r.is_anomaly)
            health = 100 - (anomaly_count * 5)  # Simple health calculation
            efficiency = 85 + (10 * (1 - anomaly_count / len(readings)))  # Simple efficiency
            
            status = UnitStatus(
                unit=unit,
                status="critical" if anomaly_count > 3 else "warning" if anomaly_count > 1 else "normal",
                sensors=[
                    SensorData(
                        unit=r.unit,
                        sensor_name=r.sensor_name,
                        value=r.value,
                        unit_measure=r.unit_measure,
                        timestamp=r.timestamp,
                        is_anomaly=r.is_anomaly
                    ) for r in readings[:9]  # Latest readings for each sensor
                ],
                overall_health=health,
                efficiency=efficiency
            )
            statuses.append(status)
    
    return statuses

@app.get("/api/sensors/latest/{unit}")
async def get_latest_sensors(unit: str, db: AsyncSession = Depends(get_db)):
    """Get latest sensor readings for a specific unit"""
    result = await db.execute(
        select(SensorReading).where(SensorReading.unit == unit).order_by(
            SensorReading.timestamp.desc()
        ).limit(50)
    )
    readings = result.scalars().all()
    
    return [
        SensorData(
            unit=r.unit,
            sensor_name=r.sensor_name,
            value=r.value,
            unit_measure=r.unit_measure,
            timestamp=r.timestamp,
            is_anomaly=r.is_anomaly
        ) for r in readings
    ]

@app.get("/api/agents/states")
async def get_agent_states():
    """Get current state of all AI agents"""
    states = await agent_orchestrator.get_all_agent_states()
    return states

@app.get("/api/agents/communications")
async def get_agent_communications(
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get recent agent communications"""
    result = await db.execute(
        select(AgentCommunication).order_by(
            AgentCommunication.timestamp.desc()
        ).limit(limit)
    )
    communications = result.scalars().all()
    
    return [
        {
            "id": c.id,
            "from_agent": c.from_agent,
            "to_agent": c.to_agent,
            "message": c.message,
            "action_taken": c.action_taken,
            "timestamp": c.timestamp,
            "severity": c.severity
        }
        for c in communications
    ]

@app.post("/api/analytics/query")
async def query_analytics(query: AnalyticsQuery):
    """Query the AI agents for analytics"""
    response = await agent_orchestrator.answer_query(query.question)
    
    return AnalyticsResponse(
        query=query.question,
        responding_agent=response.get("responding_agent", "System"),
        answer=response.get("answer", ""),
        supporting_data=response.get("sources"),
        confidence=response.get("confidence", 0.0)
    )

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/api/sensors/historical/{unit}")
async def get_historical_data(
    unit: str,
    hours: int = 24,
    db: AsyncSession = Depends(get_db)
):
    """Get historical sensor data for charts"""
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    result = await db.execute(
        select(SensorReading).where(
            and_(
                SensorReading.unit == unit,
                SensorReading.timestamp >= cutoff_time
            )
        ).order_by(SensorReading.timestamp)
    )
    readings = result.scalars().all()
    
    # Group by sensor name for chart display
    data = {}
    for reading in readings:
        if reading.sensor_name not in data:
            data[reading.sensor_name] = []
        
        data[reading.sensor_name].append({
            "timestamp": reading.timestamp.isoformat(),
            "value": reading.value,
            "is_anomaly": reading.is_anomaly
        })
    
    return data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)