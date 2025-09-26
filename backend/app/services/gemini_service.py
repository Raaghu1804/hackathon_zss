import google.generativeai as genai
from typing import Dict, Any, Optional, List
from app.config import settings
import json
import logging

logger = logging.getLogger(__name__)


class EnhancedGeminiService:
    """Enhanced Gemini service with context-aware analysis"""

    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.context_window = []  # Store conversation context
        self.max_context_length = 10

    async def analyze_with_context(self, unit: str, combined_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data with environmental and operational context"""

        prompt = f"""
        You are an expert AI agent managing the {unit} in a cement plant with access to real-time sensor data and environmental context.

        CURRENT OPERATIONAL DATA:
        Sensor Readings: {json.dumps(combined_data.get('sensor_readings', {}), indent=2)}

        ENVIRONMENTAL CONTEXT:
        Weather Conditions: {json.dumps(combined_data.get('environmental_conditions', {}), indent=2)}
        Air Quality: {json.dumps(combined_data.get('air_quality', {}), indent=2)}
        Thermal Signature: {json.dumps(combined_data.get('thermal_signature', {}), indent=2)}

        FUEL AVAILABILITY:
        {json.dumps(combined_data.get('fuel_availability', {}), indent=2)}

        Analyze this data considering:
        1. Current operational efficiency and any anomalies
        2. Impact of environmental conditions on operations
        3. Opportunities for alternative fuel utilization
        4. Chemistry balance and product quality
        5. Energy optimization potential

        Provide your analysis in JSON format:
        {{
            "status": "normal/warning/critical",
            "health_score": 0-100,
            "efficiency_score": 0-100,
            "issues": ["list of detected issues with context"],
            "recommendations": ["specific actionable recommendations"],
            "optimization_opportunities": ["opportunities based on available resources"],
            "environmental_adjustments": ["adjustments needed due to weather/conditions"],
            "fuel_switching_potential": "assessment of alternative fuel usage",
            "confidence_level": 0-1
        }}
        """

        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()

            # Clean JSON response
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]

            analysis = json.loads(result_text.strip())

            # Add to context window
            self.context_window.append({
                'unit': unit,
                'analysis': analysis,
                'timestamp': combined_data.get('timestamp')
            })

            # Maintain context window size
            if len(self.context_window) > self.max_context_length:
                self.context_window.pop(0)

            return analysis

        except Exception as e:
            logger.error(f"Error in Gemini context analysis: {e}")
            return {
                "status": "error",
                "health_score": 0,
                "efficiency_score": 0,
                "issues": ["AI analysis failed"],
                "recommendations": [],
                "optimization_opportunities": [],
                "confidence_level": 0
            }

    async def generate_optimization_plan(self,
                                         current_state: Dict[str, Any],
                                         target_metrics: Dict[str, Any],
                                         constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive optimization plan"""

        prompt = f"""
        As a cement plant optimization expert, create a detailed optimization plan.

        CURRENT STATE:
        {json.dumps(current_state, indent=2)}

        TARGET METRICS:
        - Thermal Energy: < {target_metrics.get('thermal_energy', 3.2)} GJ/tonne
        - Electrical Energy: < {target_metrics.get('electrical_energy', 95)} kWh/tonne
        - CO2 Emissions: < {target_metrics.get('co2_emission', 850)} kg/tonne
        - Alternative Fuel Rate: > {target_metrics.get('alternative_fuel_rate', 50)}%

        CONSTRAINTS:
        {json.dumps(constraints, indent=2)}

        Generate an optimization plan with:
        1. Specific parameter adjustments with expected impact
        2. Implementation sequence and timeline
        3. Risk assessment and mitigation strategies
        4. Expected ROI and payback period
        5. Monitoring KPIs

        Format as JSON with structure:
        {{
            "parameter_adjustments": {{"parameter": {{"current": value, "target": value, "impact": "description"}}}},
            "implementation_phases": [{{"phase": 1, "duration_days": N, "actions": [], "expected_results": {{}}}}],
            "risk_assessment": [{{"risk": "description", "probability": "low/medium/high", "mitigation": "strategy"}}],
            "financial_analysis": {{"investment_required": value, "annual_savings": value, "payback_months": N}},
            "success_metrics": [{{"kpi": "name", "current": value, "target": value, "measurement_frequency": "daily/weekly"}}]
        }}
        """

        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()

            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]

            return json.loads(result_text.strip())

        except Exception as e:
            logger.error(f"Error generating optimization plan: {e}")
            return {"error": str(e)}

    async def analyze_chemistry_balance(self, raw_meal_composition: Dict[str, float],
                                        target_clinker: Dict[str, float]) -> Dict[str, Any]:
        """Analyze and optimize cement chemistry balance"""

        prompt = f"""
        As a cement chemistry expert, analyze the raw meal composition and suggest optimizations.

        RAW MEAL COMPOSITION:
        {json.dumps(raw_meal_composition, indent=2)}

        TARGET CLINKER PROPERTIES:
        {json.dumps(target_clinker, indent=2)}

        Calculate and validate:
        1. Lime Saturation Factor (LSF) - target 0.92-0.98
        2. Silica Modulus (SM) - target 2.3-2.7
        3. Alumina Modulus (AM) - target 1.0-2.5
        4. Expected clinker phases (C3S, C2S, C3A, C4AF)
        5. Burnability index

        Provide recommendations for:
        - Raw material proportion adjustments
        - Process parameter optimization for quality
        - Expected strength development
        - Potential quality issues and solutions

        Format response as JSON.
        """

        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()

            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]

            return json.loads(result_text.strip())

        except Exception as e:
            logger.error(f"Error in chemistry analysis: {e}")
            return {"error": str(e)}

    async def generate_shift_report(self, shift_data: Dict[str, Any]) -> str:
        """Generate comprehensive shift report"""

        prompt = f"""
        Generate a professional shift report for cement plant operations.

        SHIFT DATA:
        {json.dumps(shift_data, indent=2)}

        Include:
        1. Executive Summary (3-4 sentences)
        2. Production Metrics
        3. Energy Consumption Analysis
        4. Quality Parameters
        5. Equipment Performance
        6. Anomalies and Actions Taken
        7. Environmental Compliance
        8. Recommendations for Next Shift

        Format as a structured report with clear sections and bullet points where appropriate.
        Use technical terminology appropriately and be concise but comprehensive.
        """

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error generating shift report: {e}")
            return f"Error generating report: {str(e)}"

    async def answer_analytics_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Enhanced query answering with public data context"""

        # Build context from conversation history
        historical_context = ""
        if self.context_window:
            recent_analyses = self.context_window[-3:]  # Last 3 analyses
            historical_context = f"""
            RECENT OPERATIONAL CONTEXT:
            {json.dumps(recent_analyses, indent=2)}
            """

        prompt = f"""
        You are an expert cement plant AI assistant with access to real-time operational data and public environmental data.

        {historical_context}

        CURRENT CONTEXT:
        {json.dumps(context, indent=2) if context else "No specific context available"}

        USER QUERY: {query}

        Provide a comprehensive answer that:
        1. Directly addresses the question with specific data and recommendations
        2. Considers environmental factors and available resources
        3. References relevant industry best practices and standards
        4. Includes quantified expected benefits where applicable
        5. Suggests monitoring metrics and success criteria

        If discussing optimization:
        - Provide specific parameter ranges and setpoints
        - Calculate expected energy savings or efficiency gains
        - Consider alternative fuel opportunities based on availability

        If discussing troubleshooting:
        - List potential root causes in order of probability
        - Provide step-by-step diagnostic approach
        - Suggest immediate and long-term corrective actions

        Be technical but clear, and always provide actionable insights.
        """

        try:
            response = self.model.generate_content(prompt)

            # Calculate confidence based on context availability
            confidence = 0.5  # Base confidence
            if context:
                if context.get('public_data_available'):
                    confidence += 0.2
                if context.get('confidence_score', 0) > 0.7:
                    confidence += 0.2
                if self.context_window:
                    confidence += 0.1

            return {
                "answer": response.text.strip(),
                "confidence": min(confidence, 0.95),
                "sources": ["Gemini AI Model", "Cement Industry Best Practices",
                            "Real-time Public Data"] if context.get('public_data_available') else ["Gemini AI Model",
                                                                                                   "Cement Industry Best Practices"],
                "context_used": bool(context),
                "historical_context_available": len(self.context_window) > 0
            }

        except Exception as e:
            logger.error(f"Error answering query: {e}")
            return {
                "answer": f"I encountered an error processing your query. Please try rephrasing or provide more context.",
                "confidence": 0.0,
                "sources": [],
                "error": str(e)
            }

    async def predict_maintenance_needs(self, equipment_data: Dict[str, Any],
                                        historical_failures: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Predict maintenance needs using historical patterns"""

        prompt = f"""
        As a predictive maintenance expert for cement plants, analyze equipment data and predict maintenance needs.

        CURRENT EQUIPMENT DATA:
        {json.dumps(equipment_data, indent=2)}

        HISTORICAL FAILURE PATTERNS:
        {json.dumps(historical_failures[-10:], indent=2)}  # Last 10 failures

        Predict:
        1. Equipment components at risk of failure (with probability)
        2. Recommended maintenance schedule for next 30 days
        3. Critical spare parts to maintain in inventory
        4. Estimated downtime if maintenance is delayed
        5. Cost-benefit analysis of preventive vs reactive maintenance

        Consider:
        - Operating hours and load factors
        - Environmental conditions impact
        - Wear patterns and degradation rates
        - Industry-standard maintenance intervals

        Format as JSON with clear risk scores and timelines.
        """

        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()

            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]

            return json.loads(result_text.strip())

        except Exception as e:
            logger.error(f"Error in maintenance prediction: {e}")
            return {
                "error": str(e),
                "maintenance_schedule": [],
                "risk_assessment": []
            }


# Global Gemini service instance
gemini_service = EnhancedGeminiService()