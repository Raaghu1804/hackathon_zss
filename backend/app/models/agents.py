# backend/app/models/agents.py

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any

class AgentMessage(BaseModel):
    from_agent: str
    to_agent: str
    message_type: str  # query, response, alert, optimization
    content: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
class AgentAction(BaseModel):
    agent: str
    action_type: str  # adjust_parameter, alert, optimize
    target_parameter: str
    current_value: float
    new_value: float
    reason: str
    expected_impact: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
class AgentState(BaseModel):
    agent_name: str
    unit: str
    status: str  # idle, analyzing, optimizing, communicating
    current_task: Optional[str] = None
    last_action: Optional[AgentAction] = None
    health_score: float = 100.0
    active_alerts: List[str] = []
    
class OptimizationRequest(BaseModel):
    requesting_agent: str
    target_unit: str
    issue: str
    current_metrics: Dict[str, float]
    suggested_adjustments: Optional[Dict[str, float]] = None
    
class AnalyticsQuery(BaseModel):
    question: str
    context: Optional[str] = None
    include_historical: bool = False
    
class AnalyticsResponse(BaseModel):
    query: str
    responding_agent: str
    answer: str
    supporting_data: Optional[Dict[str, Any]] = None
    confidence: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)