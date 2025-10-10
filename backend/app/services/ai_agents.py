import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from app.models.agents import AgentState, AgentMessage, AgentAction, OptimizationRequest
from app.models.sensors import SensorData, AnomalyAlert
from app.models.database import AsyncSessionLocal, AgentCommunication, ProcessOptimization
from app.services.gemini_service import gemini_service
from app.services.public_data_services import public_data_service
from app.services.physics_informed_models import process_optimizer, CementChemistryConstraints
from app.services.alternative_fuel_optimizer import alternative_fuel_optimizer
from app.config import settings
import json
import numpy as np
import logging

logger = logging.getLogger(__name__)


def sanitize_agent_state(state_dict: dict) -> dict:
    """Convert datetime objects to ISO strings"""
    from datetime import datetime

    sanitized = {}
    for key, value in state_dict.items():
        if isinstance(value, datetime):
            sanitized[key] = value.isoformat()
        elif isinstance(value, dict):
            sanitized[key] = sanitize_agent_state(value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_agent_state(item) if isinstance(item, dict) else
                item.isoformat() if isinstance(item, datetime) else item
                for item in value
            ]
        else:
            sanitized[key] = value
    return sanitized

class EnhancedCementPlantAgent:
    """Enhanced base class for cement plant AI agents with public data integration"""

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
        self.public_data_cache = {}
        self.last_public_data_update = None
        self.optimization_history = []
        self.confidence_score = 0.5  # Initial confidence
        self.learning_rate = 0.01
        self.uncertainty_threshold = 0.15

    async def integrate_public_data(self, plant_config: Dict[str, Any]) -> Dict[str, Any]:
        """Integrate public data sources for enhanced decision making"""
        # Check if cache is valid (less than 5 minutes old)
        if (self.last_public_data_update and
                datetime.utcnow() - self.last_public_data_update < timedelta(
                    seconds=settings.PUBLIC_DATA_REFRESH_INTERVAL)):
            return self.public_data_cache

        # Fetch new public data
        self.public_data_cache = await public_data_service.aggregate_public_data(plant_config)
        self.last_public_data_update = datetime.utcnow()

        # Validate data quality
        quality_metrics = public_data_service.validate_data_quality(self.public_data_cache)

        # Adjust confidence based on data quality
        self.confidence_score = min(0.95, 0.5 + quality_metrics['overall_score'] / 200)

        return self.public_data_cache

    async def analyze_with_public_data(self, sensor_data: List[SensorData],
                                       public_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced analysis combining sensor and public data"""
        self.state.status = "analyzing"

        # Prepare combined data for analysis
        combined_data = {
            'sensor_readings': {
                s.sensor_name: {
                    "value": s.value,
                    "unit": s.unit_measure,
                    "is_anomaly": s.is_anomaly,
                    "optimal_range": s.optimal_range
                }
                for s in sensor_data
            },
            'environmental_conditions': public_data.get('data_sources', {}).get('weather', {}),
            'air_quality': public_data.get('data_sources', {}).get('air_quality', {}),
            'thermal_signature': public_data.get('data_sources', {}).get('satellite_thermal', {}),
            'fuel_availability': public_data.get('data_sources', {}).get('alternative_fuels', {})
        }

        # Use enhanced Gemini analysis with public data context
        analysis = await gemini_service.analyze_with_context(self.unit, combined_data)

        # Physics-informed optimization
        if settings.USE_PUBLIC_DATA:
            optimization_result = await process_optimizer.optimize_with_public_data(
                public_data,
                self._extract_current_params(sensor_data)
            )
            analysis['optimization'] = optimization_result

        # Update agent state
        self.state.health_score = analysis.get("health_score", 100)
        self.state.active_alerts = analysis.get("issues", [])

        # Determine status based on analysis
        if analysis.get("status") == "critical" or self.confidence_score < 0.6:
            self.state.status = "optimizing"
        elif analysis.get("status") == "warning":
            self.state.status = "communicating"
        else:
            self.state.status = "idle"

        return analysis

    def _extract_current_params(self, sensor_data: List[SensorData]) -> Dict[str, float]:
        """Extract current parameters from sensor data"""
        params = {}
        param_mapping = {
            'burning_zone_temp': 'kiln_temperature',
            'kiln_speed': 'kiln_speed',
            'fuel_rate': 'fuel_rate',
            'feed_rate': 'feed_rate'
        }

        for sensor in sensor_data:
            if sensor.sensor_name in param_mapping:
                params[param_mapping[sensor.sensor_name]] = sensor.value

        # Set defaults for missing parameters
        defaults = {
            'kiln_temperature': 1425,
            'kiln_speed': 4.0,
            'fuel_rate': 12,
            'air_flow': 85,
            'residence_time': 30,
            'feed_rate': 300
        }

        for key, default_value in defaults.items():
            if key not in params:
                params[key] = default_value

        return params

    async def uncertainty_aware_decision(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """Make decisions with uncertainty quantification"""
        # Calculate uncertainty based on data quality and model confidence
        data_uncertainty = 1 - self.confidence_score
        model_uncertainty = 0.1  # Base model uncertainty

        total_uncertainty = np.sqrt(data_uncertainty ** 2 + model_uncertainty ** 2)

        if total_uncertainty > self.uncertainty_threshold:
            decision['requires_human_validation'] = True
            decision['confidence_level'] = 'low'
            decision['suggested_action'] = 'review'
        else:
            decision['requires_human_validation'] = False
            decision['confidence_level'] = 'high' if total_uncertainty < 0.05 else 'medium'
            decision['suggested_action'] = 'implement'

        decision['uncertainty_score'] = round(total_uncertainty, 3)

        return decision


class EnhancedPreCalcinerAgent(EnhancedCementPlantAgent):
    """Enhanced AI Agent for Pre-Calciner with public data integration"""

    def __init__(self):
        super().__init__("PreCalciner-AI-Enhanced", "precalciner")
        self.chemistry_constraints = CementChemistryConstraints()

    async def handle_anomaly(self, anomaly: AnomalyAlert, public_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle anomalies with context from public data"""
        response = {
            "action": "optimize",
            "parameters": {},
            "context_considered": []
        }

        # Consider weather conditions
        weather = public_data.get('data_sources', {}).get('weather', {})
        if weather:
            ambient_temp = weather.get('temperature', 25)
            humidity = weather.get('humidity', 60)
            response['context_considered'].append(f"Ambient: {ambient_temp}°C, {humidity}% humidity")

        # Adjust response based on anomaly type and context
        if "temperature" in anomaly.sensor_name:
            if anomaly.current_value > anomaly.expected_range["max"]:
                # High temperature - consider ambient conditions
                adjustment_factor = 1 + (ambient_temp - 25) / 100
                response["parameters"]["fuel_flow"] = f"decrease by {5 * adjustment_factor:.1f}%"
                response["parameters"]["tertiary_air_temp"] = "monitor and adjust"
            else:
                response["parameters"]["fuel_flow"] = f"increase by {5:.1f}%"

        elif "calcination_degree" in anomaly.sensor_name:
            if anomaly.current_value < anomaly.expected_range["min"]:
                # Consider alternative fuel availability
                alt_fuels = public_data.get('data_sources', {}).get('alternative_fuels', {})
                if alt_fuels and alt_fuels.get('fuels', {}).get('rice_husk', {}).get('availability_tonnes', 0) > 100:
                    response["parameters"]["alternative_fuel"] = "increase rice husk by 10%"
                    response['context_considered'].append("Rice husk available for substitution")
                else:
                    response["parameters"]["temperature"] = "increase to 880°C"
                    response["parameters"]["residence_time"] = "increase by 10%"

        # Apply uncertainty-aware decision making
        response = await self.uncertainty_aware_decision(response)

        # Communicate with other agents if high severity
        if anomaly.severity in ["high", "critical"]:
            await self.communicate_with_agent(
                "RotaryKiln-AI-Enhanced",
                "optimization",
                {
                    "issue": f"Pre-calciner anomaly: {anomaly.sensor_name}",
                    "current_value": anomaly.current_value,
                    "severity": anomaly.severity,
                    "environmental_context": weather,
                    "suggested_action": "Adjust feed rate considering upstream conditions"
                }
            )

        return response

    async def optimize_with_fuel_mix(self, current_data: Dict[str, Any],
                                     public_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize pre-calciner with alternative fuel considerations"""

        # Get fuel availability from public data
        fuel_data = public_data.get('data_sources', {}).get('alternative_fuels', {})

        if fuel_data:
            # Optimize fuel mix for pre-calciner
            result = alternative_fuel_optimizer.optimize_fuel_mix(
                total_energy_required=50,  # GJ/hour for pre-calciner
                availability_constraints={
                    fuel: data.get('availability_tonnes', 0)
                    for fuel, data in fuel_data.get('fuels', {}).items()
                },
                quality_requirements={
                    'max_ash_content': 12,
                    'max_moisture': 10
                },
                environmental_targets={'max_co2_kg_per_gj': 75}
            )

            if result.get('success'):
                return {
                    'fuel_optimization': result,
                    'recommended_changes': self._generate_fuel_recommendations(result),
                    'expected_benefits': {
                        'cost_savings': result.get('cost_savings_per_hour', 0),
                        'co2_reduction': result.get('co2_reduction', {}).get('reduction_percentage', 0)
                    }
                }

        return {'message': 'Insufficient data for fuel optimization'}

    def _generate_fuel_recommendations(self, fuel_result: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations from fuel optimization"""
        recommendations = []

        optimal_mix = fuel_result.get('optimal_mix', {})
        for fuel, percentage in optimal_mix.items():
            if percentage > 5:  # Only significant percentages
                recommendations.append(f"Use {percentage:.1f}% {fuel.replace('_', ' ')}")

        alt_fuel_rate = fuel_result.get('alternative_fuel_rate', 0)
        if alt_fuel_rate > 30:
            recommendations.append(f"High alternative fuel substitution ({alt_fuel_rate:.1f}%) achievable")

        return recommendations


class EnhancedRotaryKilnAgent(EnhancedCementPlantAgent):
    """Enhanced AI Agent for Rotary Kiln with advanced optimization"""

    def __init__(self):
        super().__init__("RotaryKiln-AI-Enhanced", "rotary_kiln")
        self.chemistry_constraints = CementChemistryConstraints()
        self.coating_model = None  # For predictive coating maintenance

    async def handle_anomaly(self, anomaly: AnomalyAlert, public_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced anomaly handling with predictive capabilities"""
        response = {
            "action": "optimize",
            "parameters": {},
            "predictive_maintenance": []
        }

        # Get satellite thermal data for external monitoring
        thermal_data = public_data.get('data_sources', {}).get('satellite_thermal', {})

        if "burning_zone_temp" in anomaly.sensor_name:
            if anomaly.current_value > anomaly.expected_range["max"]:
                response["parameters"]["fuel_rate"] = "decrease by 3%"
                response["parameters"]["kiln_speed"] = "increase by 0.2 rpm"

                # Check satellite thermal signature
                if thermal_data and thermal_data.get('median_temperature', 0) > 300:
                    response["predictive_maintenance"].append("High external temperature detected - check refractory")
            else:
                response["parameters"]["fuel_rate"] = "increase by 3%"
                response["parameters"]["secondary_air_temp"] = "check and optimize"

        elif "shell_temp" in anomaly.sensor_name and anomaly.current_value > anomaly.expected_range["max"]:
            response["action"] = "critical"
            response["parameters"]["coating_inspection"] = "required immediately"
            response["parameters"]["kiln_speed"] = "reduce to 3.5 rpm"
            response["predictive_maintenance"].append("Schedule coating repair in next shutdown")

            # Alert downstream
            await self.communicate_with_agent(
                "ClinkerCooler-AI-Enhanced",
                "alert",
                {
                    "issue": "High kiln shell temperature - potential coating loss",
                    "impact": "Expect higher clinker temperature",
                    "action_required": "Prepare for increased cooling demand",
                    "satellite_confirmation": thermal_data.get('median_temperature', 'N/A')
                }
            )

        # Chemistry optimization
        elif "clinker_quality" in str(anomaly.sensor_name).lower():
            composition_adjustment = await self.optimize_clinker_chemistry(anomaly, public_data)
            response["parameters"].update(composition_adjustment)

        return await self.uncertainty_aware_decision(response)

    async def optimize_clinker_chemistry(self, anomaly: AnomalyAlert,
                                         public_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize clinker chemistry based on quality targets"""

        # Calculate current chemistry parameters (simulated)
        current_composition = {
            'CaO': 65.0,
            'SiO2': 21.0,
            'Al2O3': 5.5,
            'Fe2O3': 3.2,
            'SO3': 2.0
        }

        # Validate chemistry
        validation = self.chemistry_constraints.validate_chemistry(current_composition)

        adjustments = {}

        if not validation['lsf']['valid']:
            lsf_current = validation['lsf']['value']
            lsf_target = validation['lsf']['optimal_range'][1] if lsf_current > validation['lsf']['optimal_range'][
                1] else validation['lsf']['optimal_range'][0]
            adjustments['limestone_ratio'] = f"adjust to achieve LSF {lsf_target:.2f}"

        if not validation['sm']['valid']:
            adjustments['silica_addition'] = "increase by 2%" if validation['sm']['value'] < \
                                                                 validation['sm']['optimal_range'][
                                                                     0] else "decrease by 2%"

        # Calculate expected clinker phases
        phases = self.chemistry_constraints.calculate_clinker_phases(current_composition)

        if phases['C3S'] < 55:
            adjustments['burning_zone_temp'] = "increase by 20°C"
            adjustments['residence_time'] = "increase by 5 minutes"

        return adjustments


class EnhancedClinkerCoolerAgent(EnhancedCementPlantAgent):
    """Enhanced AI Agent for Clinker Cooler with heat recovery optimization"""

    def __init__(self):
        super().__init__("ClinkerCooler-AI-Enhanced", "clinker_cooler")
        self.heat_recovery_target = 70  # %

    async def handle_anomaly(self, anomaly: AnomalyAlert, public_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced anomaly handling with heat recovery focus"""
        response = {
            "action": "optimize",
            "parameters": {},
            "heat_recovery_optimization": {}
        }

        # Consider air quality data for emission control
        air_quality = public_data.get('data_sources', {}).get('air_quality', {})

        if "outlet_temp" in anomaly.sensor_name:
            if anomaly.current_value > anomaly.expected_range["max"]:
                response["parameters"]["grate_speed"] = "decrease by 2 strokes/min"
                response["parameters"]["cooling_air_flow"] = "increase by 10%"

                # Calculate heat recovery potential
                heat_waste = (anomaly.current_value - 125) * 4.2  # Approximate heat loss
                response["heat_recovery_optimization"] = {
                    "potential_recovery": f"{heat_waste:.1f} GJ/hour",
                    "action": "Redirect to waste heat recovery system"
                }

        elif "cooler_efficiency" in anomaly.sensor_name:
            if anomaly.current_value < anomaly.expected_range["min"]:
                response["parameters"]["undergrate_pressure"] = "optimize distribution"
                response["parameters"]["air_distribution"] = "check all compartments"

                # Communicate upstream impact
                await self.communicate_with_agent(
                    "PreCalciner-AI-Enhanced",
                    "alert",
                    {
                        "issue": "Cooler efficiency below target",
                        "impact": f"Tertiary air temperature affected - current efficiency {anomaly.current_value}%",
                        "air_quality_status": air_quality
                    }
                )

        # Check emission limits
        if air_quality and air_quality.get('pm10', 0) > 50:
            response["parameters"]["bag_filter_cleaning"] = "initiate"
            response["action"] = "environmental_compliance"

        return await self.uncertainty_aware_decision(response)

    async def optimize_heat_recovery(self, current_data: Dict[str, Any],
                                     public_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize heat recovery from clinker cooling"""

        inlet_temp = current_data.get('inlet_temp', 1200)
        outlet_temp = current_data.get('outlet_temp', 125)
        air_flow = current_data.get('cooling_air_flow', 2.8)

        # Calculate current heat recovery
        heat_input = inlet_temp * air_flow * 1.2  # Simplified calculation
        heat_recovered = (inlet_temp - outlet_temp) * air_flow * 1.2 * 0.7
        current_efficiency = (heat_recovered / heat_input) * 100

        optimization = {
            'current_efficiency': round(current_efficiency, 1),
            'target_efficiency': self.heat_recovery_target,
            'gap': round(self.heat_recovery_target - current_efficiency, 1)
        }

        if current_efficiency < self.heat_recovery_target:
            optimization['recommendations'] = [
                f"Increase cooling air flow to {air_flow * 1.1:.2f} kg/kg",
                "Check air distribution across grate plates",
                "Optimize grate speed for uniform bed height",
                f"Target outlet temperature: {outlet_temp - 10}°C"
            ]
            optimization[
                'expected_energy_recovery'] = f"{(self.heat_recovery_target - current_efficiency) * 0.5:.1f} MW"

        return optimization


class EnhancedAIAgentOrchestrator:
    """Enhanced orchestrator with public data integration and advanced coordination"""

    def __init__(self):
        self.agents = {
            "precalciner": EnhancedPreCalcinerAgent(),
            "rotary_kiln": EnhancedRotaryKilnAgent(),
            "clinker_cooler": EnhancedClinkerCoolerAgent()
        }
        self.running = False
        self.plant_config = settings.PLANT_CONFIGS[0] if settings.PLANT_CONFIGS else {}
        self.public_data_cache = {}
        self.last_optimization = None

    async def process_with_public_data(self, unit: str, sensor_data: List[SensorData]) -> Dict[str, Any]:
        """Process sensor data with public data context"""
        if unit not in self.agents:
            return {"error": f"Unknown unit: {unit}"}

        agent = self.agents[unit]

        # Get public data
        public_data = await agent.integrate_public_data(self.plant_config)

        # Analyze with enhanced context
        analysis = await agent.analyze_with_public_data(sensor_data, public_data)

        # Check for optimization opportunities
        if analysis.get('optimization'):
            await self.coordinate_multi_unit_optimization(unit, analysis, public_data)

        return analysis

    async def coordinate_multi_unit_optimization(self, initiating_unit: str,
                                                 analysis: Dict[str, Any],
                                                 public_data: Dict[str, Any]):
        """Coordinate optimization across multiple units with public data context"""

        optimization_plan = {
            'initiating_unit': initiating_unit,
            'timestamp': datetime.utcnow(),
            'actions': []
        }

        # Get optimization suggestions from physics-informed model
        if analysis.get('optimization', {}).get('optimal_parameters'):
            optimal_params = analysis['optimization']['optimal_parameters']

            # Coordinate changes across units
            if initiating_unit == "precalciner":
                # Adjust kiln for precalciner optimization
                kiln_adjustment = {
                    'unit': 'rotary_kiln',
                    'adjustments': {
                        'feed_rate': optimal_params.get('feed_rate', 300) * 0.98,  # Slight reduction
                        'fuel_rate': 'monitor and adjust'
                    }
                }
                optimization_plan['actions'].append(kiln_adjustment)

            elif initiating_unit == "rotary_kiln":
                # Adjust both precalciner and cooler
                precalciner_adjustment = {
                    'unit': 'precalciner',
                    'adjustments': {
                        'temperature': 'increase by 10°C' if optimal_params.get('kiln_temperature',
                                                                                1425) > 1450 else 'maintain',
                        'calcination_degree': 'target 93%'
                    }
                }
                cooler_adjustment = {
                    'unit': 'clinker_cooler',
                    'adjustments': {
                        'cooling_air_flow': 'prepare for higher load' if optimal_params.get('kiln_temperature',
                                                                                            1425) > 1450 else 'maintain',
                        'grate_speed': 'increase by 2 strokes/min'
                    }
                }
                optimization_plan['actions'].extend([precalciner_adjustment, cooler_adjustment])

            # Store optimization plan
            self.last_optimization = optimization_plan

            # Communicate plan to all agents
            for action in optimization_plan['actions']:
                target_agent = self.agents.get(action['unit'])
                if target_agent:
                    await target_agent.communicate_with_agent(
                        f"{initiating_unit}-AI",
                        "coordination",
                        {
                            "optimization_plan": action['adjustments'],
                            "reason": analysis.get('optimization', {}).get('improvements', {}),
                            "public_data_context": {
                                'weather': public_data.get('data_sources', {}).get('weather', {}),
                                'fuel_availability': public_data.get('data_sources', {}).get('alternative_fuels', {})
                            }
                        }
                    )

    async def comprehensive_plant_optimization(self) -> Dict[str, Any]:
        """Perform comprehensive plant-wide optimization using all available data"""

        # Gather public data
        public_data = await public_data_service.aggregate_public_data(self.plant_config)

        # Optimize fuel mix
        fuel_optimization = alternative_fuel_optimizer.optimize_fuel_mix(
            total_energy_required=200,  # GJ/hour total plant
            availability_constraints={
                'coal': 1000000,  # Unlimited
                'rice_husk': public_data.get('data_sources', {}).get('alternative_fuels', {}).get('fuels', {}).get(
                    'rice_husk', {}).get('availability_tonnes', 0),
                'rdf': public_data.get('data_sources', {}).get('alternative_fuels', {}).get('fuels', {}).get(
                    'municipal_waste', {}).get('availability_tonnes', 0),
                'biomass': public_data.get('data_sources', {}).get('alternative_fuels', {}).get('fuels', {}).get(
                    'biomass', {}).get('availability_tonnes', 0)
            },
            quality_requirements=settings.constraints,
            environmental_targets={'max_co2_kg_per_gj': 75}
        )

        # Process optimization using physics-informed models
        process_optimization = await process_optimizer.optimize_with_public_data(public_data)

        # Compile comprehensive report
        return {
            'timestamp': datetime.utcnow(),
            'plant_id': self.plant_config.get('plant_id'),
            'fuel_optimization': fuel_optimization,
            'process_optimization': process_optimization,
            'environmental_impact': {
                'current_emissions': public_data.get('data_sources', {}).get('air_quality', {}),
                'projected_reduction': fuel_optimization.get('co2_reduction', {}).get('reduction_percentage', 0)
            },
            'confidence_score': np.mean([agent.confidence_score for agent in self.agents.values()]),
            'recommendations': self._generate_comprehensive_recommendations(fuel_optimization, process_optimization)
        }

    def _generate_comprehensive_recommendations(self, fuel_opt: Dict[str, Any],
                                                process_opt: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations from comprehensive optimization"""
        recommendations = []

        # Fuel recommendations
        if fuel_opt.get('success'):
            if fuel_opt.get('alternative_fuel_rate', 0) > 30:
                recommendations.append(
                    f"Achieve {fuel_opt['alternative_fuel_rate']:.1f}% alternative fuel substitution")
            if fuel_opt.get('annual_savings', 0) > 1000000:
                recommendations.append(f"Potential annual savings: ${fuel_opt['annual_savings']:,.0f}")

        # Process recommendations
        if process_opt.get('optimal_parameters'):
            for param, value in process_opt['optimal_parameters'].items():
                recommendations.append(f"Optimize {param.replace('_', ' ')}: {value:.2f}")

        if process_opt.get('improvements', {}).get('percentage_improvement', 0) > 5:
            recommendations.append(
                f"Expected efficiency improvement: {process_opt['improvements']['percentage_improvement']:.1f}%")

        return recommendations

    async def get_all_agent_states(self) -> Dict[str, Any]:
        """Get current state of all agents - datetime safe"""
        states = {}
        for unit, agent in self.agents.items():
            state_dict = agent.state.dict()
            state_dict['confidence_score'] = agent.confidence_score

            if agent.last_public_data_update:
                state_dict['last_public_data_update'] = agent.last_public_data_update.isoformat()
            else:
                state_dict['last_public_data_update'] = None

            states[unit] = sanitize_agent_state(state_dict)

        return states

    async def answer_query(self, query: str) -> Dict[str, Any]:
        """Answer user query with public data context"""
        # Determine which agent should answer
        query_lower = query.lower()

        agent_mapping = {
            'calcin': 'precalciner',
            'pre': 'precalciner',
            'kiln': 'rotary_kiln',
            'burning': 'rotary_kiln',
            'clinker': 'rotary_kiln',
            'cool': 'clinker_cooler',
            'grate': 'clinker_cooler',
            'heat': 'clinker_cooler'
        }

        selected_unit = 'rotary_kiln'  # Default
        for keyword, unit in agent_mapping.items():
            if keyword in query_lower and not (keyword == 'clinker' and 'cooler' not in query_lower):
                selected_unit = unit
                break

        agent = self.agents[selected_unit]

        # Get public data context
        public_data = await agent.integrate_public_data(self.plant_config)

        # Prepare context
        context = {
            'agent': agent.name,
            'unit': selected_unit,
            'public_data_available': bool(public_data),
            'confidence_score': agent.confidence_score,
            'environmental_conditions': public_data.get('data_sources', {}).get('weather', {}),
            'fuel_availability': public_data.get('data_sources', {}).get('alternative_fuels', {})
        }

        # Get response from Gemini
        response = await gemini_service.answer_analytics_query(query, context)
        response['responding_agent'] = agent.name
        response['data_sources_used'] = list(public_data.get('data_sources', {}).keys()) if public_data else []

        return response


# Global orchestrator instance
agent_orchestrator = EnhancedAIAgentOrchestrator()