from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
import asyncio
import json
from datetime import datetime, timedelta
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
import numpy as np

from app.config import settings
from app.models.database import Base, engine, get_db, SensorReading, AgentCommunication, ProcessOptimization
from app.models.sensors import SensorData, UnitStatus, AnomalyAlert
from app.models.agents import AnalyticsQuery, AnalyticsResponse, AgentState
from app.services.data_simulator import simulator
from app.services.ai_agents import agent_orchestrator
from app.services.public_data_services import public_data_service
from app.services.physics_informed_models import process_optimizer
from app.services.alternative_fuel_optimizer import alternative_fuel_optimizer
from app.services.gemini_service import gemini_service

app = FastAPI(
    title="Cement AI Optimizer - Enhanced Edition",
    version="2.0.0",
    description="AI-Driven Cement Plant Optimization Platform with Public Data Integration"
)

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

# Background tasks
background_tasks = set()


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database and start background tasks"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Start data simulation
    task1 = asyncio.create_task(simulator.simulate_continuous_data())
    background_tasks.add(task1)

    # Start sensor data broadcast
    task2 = asyncio.create_task(broadcast_sensor_data())
    background_tasks.add(task2)

    # Start public data refresh if enabled
    if settings.USE_PUBLIC_DATA:
        task3 = asyncio.create_task(refresh_public_data())
        background_tasks.add(task3)


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Stop simulation and background tasks"""
    simulator.stop_simulation()
    for task in background_tasks:
        task.cancel()


# Background task to refresh public data
async def refresh_public_data():
    """Periodically refresh public data sources"""
    while True:
        try:
            plant_config = settings.PLANT_CONFIGS[0] if settings.PLANT_CONFIGS else {}
            if plant_config:
                public_data = await public_data_service.aggregate_public_data(plant_config)

                # Process with AI agents if data quality is good
                quality = public_data_service.validate_data_quality(public_data)
                if quality['overall_score'] > 70:
                    # Trigger optimization with new data
                    optimization = await agent_orchestrator.comprehensive_plant_optimization()

                    # Broadcast optimization recommendations
                    await manager.broadcast({
                        "type": "optimization_update",
                        "timestamp": datetime.utcnow().isoformat(),
                        "optimization": optimization,
                        "data_quality": quality
                    })

            await asyncio.sleep(settings.PUBLIC_DATA_REFRESH_INTERVAL)

        except Exception as e:
            print(f"Error refreshing public data: {e}")
            await asyncio.sleep(settings.PUBLIC_DATA_REFRESH_INTERVAL)


# Background task to broadcast sensor data
async def broadcast_sensor_data():
    """Broadcast sensor data to all connected clients with public data context"""
    while True:
        try:
            # Get latest sensor readings
            async with AsyncSessionLocal() as session:
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

                    # Process through enhanced AI agents with public data
                    anomalies = []
                    optimization_suggestions = []

                    for unit, data in units_data.items():
                        # Process with public data context
                        analysis = await agent_orchestrator.process_with_public_data(unit, data)

                        # Check for anomalies
                        unit_anomalies = simulator.detect_anomalies(data)
                        if unit_anomalies:
                            anomalies.extend(unit_anomalies)

                            # Get public data for context
                            plant_config = settings.PLANT_CONFIGS[0] if settings.PLANT_CONFIGS else {}
                            public_data = await public_data_service.aggregate_public_data(plant_config)

                            # Handle through agents with context
                            responses = await agent_orchestrator.handle_anomalies(unit_anomalies)

                            # Add optimization suggestions
                            if analysis.get('optimization'):
                                optimization_suggestions.append({
                                    'unit': unit,
                                    'suggestions': analysis['optimization']
                                })

                    # Broadcast to WebSocket clients
                    await manager.broadcast({
                        "type": "sensor_update",
                        "timestamp": datetime.utcnow().isoformat(),
                        "data": {
                            unit: [s.dict() for s in sensors]
                            for unit, sensors in units_data.items()
                        },
                        "anomalies": [a.dict() for a in anomalies] if anomalies else [],
                        "optimizations": optimization_suggestions
                    })

            await asyncio.sleep(settings.SIMULATION_INTERVAL)

        except Exception as e:
            print(f"Error in broadcast task: {e}")
            await asyncio.sleep(settings.SIMULATION_INTERVAL)


# API Endpoints

@app.get("/")
async def root():
    return {
        "message": "Cement AI Optimizer API - Enhanced Edition",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "Public Data Integration",
            "Physics-Informed Models",
            "Alternative Fuel Optimization",
            "Bayesian Optimization",
            "Uncertainty Quantification"
        ]
    }


@app.get("/api/public-data/current")
async def get_current_public_data():
    """Get current public data for the plant"""
    plant_config = settings.PLANT_CONFIGS[0] if settings.PLANT_CONFIGS else {}
    if not plant_config:
        raise HTTPException(status_code=400, detail="No plant configuration found")

    public_data = await public_data_service.aggregate_public_data(plant_config)
    quality = public_data_service.validate_data_quality(public_data)

    return {
        "plant_id": plant_config.get("plant_id"),
        "data": public_data,
        "quality_metrics": quality,
        "timestamp": datetime.utcnow()
    }


@app.get("/api/public-data/satellite/{days_back}")
async def get_satellite_analysis(days_back: int = 7):
    """Get satellite thermal analysis for the plant"""
    plant_config = settings.PLANT_CONFIGS[0] if settings.PLANT_CONFIGS else {}
    if not plant_config or 'location' not in plant_config:
        raise HTTPException(status_code=400, detail="Plant location not configured")

    lat = plant_config['location']['lat']
    lon = plant_config['location']['lon']

    thermal_data = await public_data_service.get_satellite_thermal_signature(lat, lon, days_back)

    return thermal_data


@app.post("/api/optimization/fuel-mix")
async def optimize_fuel_mix(
        total_energy: float = 200,  # GJ/hour
        max_co2: Optional[float] = None
):
    """Optimize alternative fuel mix"""
    plant_config = settings.PLANT_CONFIGS[0] if settings.PLANT_CONFIGS else {}
    region = plant_config.get('region', 'default')

    # Get fuel availability from public data
    fuel_availability = await public_data_service.get_alternative_fuel_availability(region)

    # Build constraints
    availability_constraints = {
        fuel: data.get('availability_tonnes', 0)
        for fuel, data in fuel_availability.get('fuels', {}).items()
    }
    availability_constraints['coal'] = 1000000  # Unlimited coal

    # Quality requirements from settings
    quality_requirements = {
        'max_ash_content': 15,
        'max_moisture': 12
    }

    # Environmental targets
    environmental_targets = {'max_co2_kg_per_gj': max_co2} if max_co2 else None

    # Optimize
    result = alternative_fuel_optimizer.optimize_fuel_mix(
        total_energy_required=total_energy,
        availability_constraints=availability_constraints,
        quality_requirements=quality_requirements,
        environmental_targets=environmental_targets
    )

    return result


@app.post("/api/optimization/process")
async def optimize_process(
        background_tasks: BackgroundTasks,
        include_public_data: bool = True
):
    """Optimize process parameters using physics-informed models"""

    if include_public_data:
        plant_config = settings.PLANT_CONFIGS[0] if settings.PLANT_CONFIGS else {}
        public_data = await public_data_service.aggregate_public_data(plant_config)
    else:
        public_data = {}

    # Get current parameters from latest sensor readings
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(SensorReading).order_by(SensorReading.timestamp.desc()).limit(100)
        )
        readings = result.scalars().all()

    current_params = {}
    if readings:
        # Extract key parameters
        for reading in readings:
            if 'temp' in reading.sensor_name and 'burning' in reading.sensor_name:
                current_params['kiln_temperature'] = reading.value
            elif 'kiln_speed' in reading.sensor_name:
                current_params['kiln_speed'] = reading.value
            elif 'fuel_rate' in reading.sensor_name:
                current_params['fuel_rate'] = reading.value

    # Optimize
    optimization = await process_optimizer.optimize_with_public_data(public_data, current_params)

    # Store optimization in background
    background_tasks.add_task(store_optimization_results, optimization)

    return optimization


async def store_optimization_results(optimization: Dict[str, Any]):
    """Store optimization results in database"""
    async with AsyncSessionLocal() as session:
        for param, value in optimization.get('optimal_parameters', {}).items():
            db_opt = ProcessOptimization(
                unit='plant_wide',
                parameter=param,
                original_value=0,  # Would get from current_params
                optimized_value=value,
                reason='Bayesian optimization',
                impact=f"Expected improvement: {optimization.get('improvements', {}).get('percentage_improvement', 0):.1f}%"
            )
            session.add(db_opt)
        await session.commit()


@app.post("/api/optimization/comprehensive")
async def comprehensive_optimization():
    """Perform comprehensive plant-wide optimization"""
    result = await agent_orchestrator.comprehensive_plant_optimization()
    return result


@app.get("/api/chemistry/validate")
async def validate_chemistry(
        cao: float = 65.0,
        sio2: float = 21.0,
        al2o3: float = 5.5,
        fe2o3: float = 3.2,
        so3: float = 2.0
):
    """Validate cement chemistry parameters"""
    from app.services.physics_informed_models import CementChemistryConstraints

    composition = {
        'CaO': cao,
        'SiO2': sio2,
        'Al2O3': al2o3,
        'Fe2O3': fe2o3,
        'SO3': so3
    }

    constraints = CementChemistryConstraints()
    validation = constraints.validate_chemistry(composition)
    phases = constraints.calculate_clinker_phases(composition)

    return {
        'composition': composition,
        'validation': validation,
        'clinker_phases': phases,
        'recommendations': generate_chemistry_recommendations(validation, phases)
    }


def generate_chemistry_recommendations(validation: Dict, phases: Dict) -> List[str]:
    """Generate recommendations based on chemistry validation"""
    recommendations = []

    if not validation['lsf']['valid']:
        if validation['lsf']['value'] < validation['lsf']['optimal_range'][0]:
            recommendations.append("Increase limestone content to raise LSF")
        else:
            recommendations.append("Reduce limestone or increase clay content to lower LSF")

    if phases['C3S'] < 55:
        recommendations.append("Increase burning zone temperature or LSF to boost C3S content")

    if phases['C3A'] > 12:
        recommendations.append("Reduce alumina content to control C3A for sulfate resistance")

    return recommendations


@app.get("/api/reports/shift")
async def generate_shift_report(
        shift_start: Optional[datetime] = None,
        shift_end: Optional[datetime] = None,
        db: AsyncSession = Depends(get_db)
):
    """Generate comprehensive shift report"""

    if not shift_end:
        shift_end = datetime.utcnow()
    if not shift_start:
        shift_start = shift_end - timedelta(hours=8)

    # Gather shift data
    result = await db.execute(
        select(SensorReading).where(
            and_(
                SensorReading.timestamp >= shift_start,
                SensorReading.timestamp <= shift_end
            )
        )
    )
    readings = result.scalars().all()

    # Calculate shift metrics
    shift_data = calculate_shift_metrics(readings)

    # Generate report using Gemini
    report = await gemini_service.generate_shift_report(shift_data)

    return {
        "shift_period": {
            "start": shift_start,
            "end": shift_end
        },
        "metrics": shift_data,
        "report": report
    }


def calculate_shift_metrics(readings: List[SensorReading]) -> Dict[str, Any]:
    """Calculate metrics for shift report"""
    metrics = {
        'total_readings': len(readings),
        'anomaly_count': sum(1 for r in readings if r.is_anomaly),
        'units': {}
    }

    # Group by unit
    for reading in readings:
        if reading.unit not in metrics['units']:
            metrics['units'][reading.unit] = {
                'readings': [],
                'anomalies': 0,
                'avg_values': {}
            }

        metrics['units'][reading.unit]['readings'].append(reading.value)
        if reading.is_anomaly:
            metrics['units'][reading.unit]['anomalies'] += 1

    # Calculate averages
    for unit in metrics['units']:
        if metrics['units'][unit]['readings']:
            metrics['units'][unit]['avg_values'] = {
                'mean': np.mean(metrics['units'][unit]['readings']),
                'std': np.std(metrics['units'][unit]['readings']),
                'min': np.min(metrics['units'][unit]['readings']),
                'max': np.max(metrics['units'][unit]['readings'])
            }

    return metrics


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Enhanced WebSocket endpoint with public data updates"""
    await manager.connect(websocket)
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
            await asyncio.sleep(1)

    except WebSocketDisconnect:
        manager.disconnect(websocket)


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
            "simulation": "running"
        }
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)