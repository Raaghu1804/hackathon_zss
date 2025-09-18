# backend/app/services/ai_agents.py

import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from app.models.agents import AgentState, AgentMessage, AgentAction, OptimizationRequest
from app.models.sensors import SensorData, AnomalyAlert
from app.models.database import AsyncSessionLocal, AgentCommunication, ProcessOptimization
from app.services.gemini_service import gemini_service
from app.config import settings
import json

class CementPlantAgent:
    """Base class for cement plant AI agents"""
    
    def __init__(self, name: str, unit: str):
        self.name = name
        self.unit = unit
        self.state = AgentState(
            agent_name=name,
            unit=unit,
            status="idle",
            health_score=100.0,
            active_alerts=[]
        )
        self.communication_queue = asyncio.Queue()
        self.sensor_data_cache = {}
        
    async def analyze_data(self, sensor_data: List[SensorData]) -> Dict[str, Any]:
        """Analyze sensor data for the unit"""
        self.state.status = "analyzing"
        
        # Convert sensor data to dict for analysis
        data_dict = {
            s.sensor_name: {
                "value": s.value,
                "unit": s.unit_measure,
                "is_anomaly": s.is_anomaly,
                "optimal_range": s.optimal_range
            }
            for s in sensor_data
        }
        
        # Use Gemini for analysis
        analysis = await gemini_service.analyze_sensor_data(self.unit, data_dict)
        
        # Update agent state based on analysis
        self.state.health_score = analysis.get("health_score", 100)
        self.state.active_alerts = analysis.get("issues", [])
        
        if analysis.get("status") == "critical":
            self.state.status = "optimizing"
        elif analysis.get("status") == "warning":
            self.state.status = "communicating"
        else:
            self.state.status = "idle"
        
        return analysis
    
    async def communicate_with_agent(self, target_agent: str, message_type: str, content: Dict[str, Any]):
        """Send message to another agent"""
        message = AgentMessage(
            from_agent=self.name,
            to_agent=target_agent,
            message_type=message_type,
            content=json.dumps(content),
            data=content
        )
        
        # Store in database
        async with AsyncSessionLocal() as session:
            db_comm = AgentCommunication(
                from_agent=message.from_agent,
                to_agent=message.to_agent,
                message=message.content,
                severity=content.get("severity", "info")
            )
            session.add(db_comm)
            await session.commit()
        
        return message
    
    async def optimize_parameters(self, issue: str, current_params: Dict[str, float]) -> Dict[str, Any]:
        """Optimize unit parameters based on detected issues"""
        self.state.status = "optimizing"
        
        optimization = await gemini_service.suggest_optimization(
            self.unit,
            current_params,
            issue
        )
        
        # Store optimization in database
        async with AsyncSessionLocal() as session:
            for param, changes in optimization.get("adjustments", {}).items():
                db_opt = ProcessOptimization(
                    unit=self.unit,
                    parameter=param,
                    original_value=changes.get("current", 0),
                    optimized_value=changes.get("suggested", 0),
                    reason=issue,
                    impact=", ".join(optimization.get("expected_benefits", []))
                )
                session.add(db_opt)
            await session.commit()
        
        self.state.status = "idle"
        return optimization

class PreCalcinerAgent(CementPlantAgent):
    """AI Agent for Pre-Calciner unit"""
    
    def __init__(self):
        super().__init__("PreCalciner-AI", "precalciner")
        
    async def handle_anomaly(self, anomaly: AnomalyAlert) -> Dict[str, Any]:
        """Handle anomalies specific to pre-calciner"""
        response = {
            "action": "adjust",
            "parameters": {}
        }
        
        if "temperature" in anomaly.sensor_name:
            if anomaly.current_value > anomaly.expected_range["max"]:
                response["parameters"]["fuel_flow"] = "decrease by 5%"
                response["parameters"]["tertiary_air_temp"] = "monitor"
            else:
                response["parameters"]["fuel_flow"] = "increase by 5%"
                
        elif "calcination_degree" in anomaly.sensor_name:
            if anomaly.current_value < anomaly.expected_range["min"]:
                response["parameters"]["residence_time"] = "increase"
                response["parameters"]["temperature"] = "increase to 880°C"
                
        # Communicate with Rotary Kiln if needed
        if anomaly.severity in ["high", "critical"]:
            await self.communicate_with_agent(
                "RotaryKiln-AI",
                "optimization",
                {
                    "issue": f"Pre-calciner anomaly: {anomaly.sensor_name}",
                    "current_value": anomaly.current_value,
                    "severity": anomaly.severity,
                    "suggested_action": "Adjust feed rate to compensate"
                }
            )
        
        return response

class RotaryKilnAgent(CementPlantAgent):
    """AI Agent for Rotary Kiln unit"""
    
    def __init__(self):
        super().__init__("RotaryKiln-AI", "rotary_kiln")
        
    async def handle_anomaly(self, anomaly: AnomalyAlert) -> Dict[str, Any]:
        """Handle anomalies specific to rotary kiln"""
        response = {
            "action": "adjust",
            "parameters": {}
        }
        
        if "burning_zone_temp" in anomaly.sensor_name:
            if anomaly.current_value > anomaly.expected_range["max"]:
                response["parameters"]["fuel_rate"] = "decrease by 3%"
                response["parameters"]["kiln_speed"] = "increase by 0.2 rpm"
            else:
                response["parameters"]["fuel_rate"] = "increase by 3%"
                response["parameters"]["secondary_air_temp"] = "check and optimize"
                
        elif "shell_temp" in anomaly.sensor_name and anomaly.current_value > anomaly.expected_range["max"]:
            response["action"] = "critical"
            response["parameters"]["coating_inspection"] = "required"
            response["parameters"]["kiln_speed"] = "reduce immediately"
            
            # Alert Clinker Cooler
            await self.communicate_with_agent(
                "ClinkerCooler-AI",
                "alert",
                {
                    "issue": "High kiln shell temperature detected",
                    "impact": "Potential refractory damage",
                    "action_required": "Prepare for higher clinker temperature"
                }
            )
        
        return response

class ClinkerCoolerAgent(CementPlantAgent):
    """AI Agent for Clinker Cooler unit"""
    
    def __init__(self):
        super().__init__("ClinkerCooler-AI", "clinker_cooler")
        
    async def handle_anomaly(self, anomaly: AnomalyAlert) -> Dict[str, Any]:
        """Handle anomalies specific to clinker cooler"""
        response = {
            "action": "adjust",
            "parameters": {}
        }
        
        if "outlet_temp" in anomaly.sensor_name:
            if anomaly.current_value > anomaly.expected_range["max"]:
                response["parameters"]["grate_speed"] = "decrease by 2 strokes/min"
                response["parameters"]["cooling_air_flow"] = "increase by 10%"
                response["parameters"]["bed_height"] = "monitor and adjust"
                
        elif "cooler_efficiency" in anomaly.sensor_name:
            if anomaly.current_value < anomaly.expected_range["min"]:
                response["parameters"]["undergrate_pressure"] = "optimize distribution"
                response["parameters"]["air_distribution"] = "check all compartments"
                
                # Communicate with both units
                await self.communicate_with_agent(
                    "PreCalciner-AI",
                    "alert",
                    {
                        "issue": "Cooler efficiency low",
                        "impact": "Tertiary air temperature may be affected",
                        "current_efficiency": anomaly.current_value
                    }
                )
        
        return response

class AIAgentOrchestrator:
    """Orchestrator for all AI agents"""
    
    def __init__(self):
        self.agents = {
            "precalciner": PreCalcinerAgent(),
            "rotary_kiln": RotaryKilnAgent(),
            "clinker_cooler": ClinkerCoolerAgent()
        }
        self.running = False
        
    async def process_sensor_data(self, unit: str, sensor_data: List[SensorData]) -> Dict[str, Any]:
        """Process sensor data through appropriate agent"""
        if unit not in self.agents:
            return {"error": f"Unknown unit: {unit}"}
        
        agent = self.agents[unit]
        analysis = await agent.analyze_data(sensor_data)
        
        # Check for cross-unit optimization opportunities
        if analysis.get("optimization_opportunities"):
            await self.coordinate_optimization(unit, analysis)
        
        return analysis
    
    async def coordinate_optimization(self, initiating_unit: str, analysis: Dict[str, Any]):
        """Coordinate optimization across multiple units"""
        # Example: If pre-calciner needs optimization, coordinate with kiln
        if initiating_unit == "precalciner" and "temperature" in str(analysis.get("issues", [])):
            # Get kiln agent to adjust
            kiln_agent = self.agents["rotary_kiln"]
            await kiln_agent.communicate_with_agent(
                "PreCalciner-AI",
                "coordination",
                {
                    "message": "Adjusting kiln parameters to support pre-calciner optimization",
                    "adjustments": {"feed_rate": "reduce by 2%", "fuel_rate": "monitor"}
                }
            )
    
    async def handle_anomalies(self, anomalies: List[AnomalyAlert]):
        """Handle detected anomalies through agents"""
        responses = {}
        
        for anomaly in anomalies:
            if anomaly.unit in self.agents:
                agent = self.agents[anomaly.unit]
                response = await agent.handle_anomaly(anomaly)
                responses[anomaly.unit] = response
        
        return responses
    
    async def get_all_agent_states(self) -> Dict[str, AgentState]:
        """Get current state of all agents"""
        return {
            unit: agent.state.dict()
            for unit, agent in self.agents.items()
        }
    
    async def answer_query(self, query: str) -> Dict[str, Any]:
        """Answer user query by selecting appropriate agent"""
        # Determine which agent should answer based on query content
        query_lower = query.lower()
        
        if "calcin" in query_lower or "pre" in query_lower:
            agent_name = "PreCalciner-AI"
        elif "kiln" in query_lower or "burning" in query_lower or "clinker" in query_lower and "cooler" not in query_lower:
            agent_name = "RotaryKiln-AI"
        elif "cool" in query_lower or "grate" in query_lower:
            agent_name = "ClinkerCooler-AI"
        else:
            # General query - use primary kiln agent
            agent_name = "RotaryKiln-AI"
        
        # Get recent data for context
        context = {
            "agent": agent_name,
            "unit": agent_name.replace("-AI", "").lower().replace(" ", "_")
        }
        
        response = await gemini_service.answer_analytics_query(query, context)
        response["responding_agent"] = agent_name
        
        return response

# Global orchestrator instance
agent_orchestrator = AIAgentOrchestrator()