# backend/app/models/sensors.py

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict

class SensorData(BaseModel):
    unit: str
    sensor_name: str
    value: float
    unit_measure: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    is_anomaly: bool = False
    optimal_range: Optional[Dict[str, float]] = None
    
class UnitStatus(BaseModel):
    unit: str
    status: str  # normal, warning, critical
    sensors: List[SensorData]
    overall_health: float  # 0-100%
    efficiency: float  # 0-100%
    
class SensorThreshold(BaseModel):
    sensor_name: str
    min_value: float
    max_value: float
    unit: str
    
class AnomalyAlert(BaseModel):
    unit: str
    sensor_name: str
    current_value: float
    expected_range: Dict[str, float]
    severity: str  # low, medium, high, critical
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    suggested_action: Optional[str] = None