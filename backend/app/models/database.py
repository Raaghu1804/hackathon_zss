# backend/app/models/database.py

from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from app.config import settings

Base = declarative_base()

# Async engine
engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

class SensorReading(Base):
    __tablename__ = "sensor_readings"
    
    id = Column(Integer, primary_key=True, index=True)
    unit = Column(String, index=True)  # precalciner, rotary_kiln, clinker_cooler
    sensor_name = Column(String, index=True)
    value = Column(Float)
    unit_measure = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_anomaly = Column(Boolean, default=False)
    
class AgentCommunication(Base):
    __tablename__ = "agent_communications"
    
    id = Column(Integer, primary_key=True, index=True)
    from_agent = Column(String)
    to_agent = Column(String)
    message = Column(Text)
    action_taken = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    severity = Column(String, default="info")  # info, warning, critical
    
class ProcessOptimization(Base):
    __tablename__ = "process_optimizations"
    
    id = Column(Integer, primary_key=True, index=True)
    unit = Column(String)
    parameter = Column(String)
    original_value = Column(Float)
    optimized_value = Column(Float)
    reason = Column(Text)
    impact = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    applied = Column(Boolean, default=False)