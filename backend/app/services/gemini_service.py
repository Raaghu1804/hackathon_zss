import google.generativeai as genai
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.config import settings
import json
import logging

logger = logging.getLogger(__name__)


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects"""

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def sanitize_for_json(data: Any) -> Any:
    """Recursively convert datetime objects to strings"""
    if isinstance(data, datetime):
        return data.isoformat()
    elif isinstance(data, dict):
        return {key: sanitize_for_json(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_for_json(item) for item in data]
    elif isinstance(data, tuple):
        return tuple(sanitize_for_json(item) for item in data)
    else:
        return data


class EnhancedGeminiService:
    """Enhanced Gemini service with context-aware analysis"""

    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.context_window = []  # Store conversation context
        self.max_context_length = 10

    async def analyze_with_context(self, unit: str, combined_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data with environmental and operational context"""

        # Sanitize data to remove datetime objects
        sanitized_data = sanitize_for_json(combined_data)

        prompt = f"""
        You are an expert AI agent managing the {unit} in a cement plant with access to real-time sensor data and environmental context.

        CURRENT OPERATIONAL DATA:
        Sensor Readings: {json.dumps(sanitized_data.get('sensor_readings', {}), indent=2)}

        ENVIRONMENTAL CONTEXT:
        Weather Conditions: {json.dumps(sanitized_data.get('environmental_conditions', {}), indent=2)}
        Air Quality: {json.dumps(sanitized_data.get('air_quality', {}), indent=2)}
        Thermal Signature: {json.dumps(sanitized_data.get('thermal_signature', {}), indent=2)}

        FUEL AVAILABILITY:
        {json.dumps(sanitized_data.get('fuel_availability', {}), indent=2)}

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
                'timestamp': datetime.utcnow().isoformat()
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

    async def answer_analytics_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Answer analytics queries with full context and better formatting"""

        # Sanitize context to remove datetime objects
        if context:
            context = sanitize_for_json(context)

        # Build historical context summary
        historical_context = ""
        if self.context_window:
            recent_analyses = self.context_window[-3:]
            historical_context = "RECENT SYSTEM STATE:\n"
            for ctx in recent_analyses:
                historical_context += f"- {ctx['unit']}: {ctx['analysis'].get('status', 'unknown')} status\n"

        # Create simplified context string
        context_str = "No specific context available"
        if context:
            try:
                context_parts = []
                if context.get('agent'):
                    context_parts.append(f"Agent: {context['agent']}")
                if context.get('unit'):
                    context_parts.append(f"Unit: {context['unit']}")
                if context.get('public_data_available'):
                    context_parts.append("Public data: Available")
                if context.get('confidence_score'):
                    context_parts.append(f"Confidence: {context['confidence_score']}")

                context_str = "\n".join(context_parts)
            except Exception as e:
                logger.warning(f"Error formatting context: {e}")
                context_str = "Context available but formatting failed"

        # IMPROVED PROMPT FOR BETTER FORMATTING
        prompt = f"""
    You are an expert cement plant operations AI assistant. Provide clear, well-structured responses.

    {historical_context}

    CURRENT CONTEXT:
    {context_str}

    USER QUERY: {query}

    INSTRUCTIONS FOR YOUR RESPONSE:
    1. Keep your response clear and well-organized
    2. Use numbered sections (1., 2., 3., etc.) for multiple points
    3. Keep each section concise (2-3 sentences maximum)
    4. Use simple formatting - avoid excessive asterisks
    5. Focus on actionable insights
    6. Provide specific numbers and parameters when relevant

    FORMAT YOUR RESPONSE LIKE THIS:

    **Summary:**
    [Brief 1-2 sentence answer to the question]

    **Key Points:**
    1. [First important point with specific data]
    2. [Second important point with recommendations]
    3. [Third point if needed]

    **Recommendations:**
    - [Specific actionable step 1]
    - [Specific actionable step 2]

    **Expected Benefits:**
    [Brief statement of expected improvements]

    Now answer the query above following this format. Keep it professional but concise.
    """

        try:
            response = self.model.generate_content(prompt)

            # Calculate confidence
            confidence = 0.5
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
                            "Real-time Public Data"] if context and context.get('public_data_available') else [
                    "Gemini AI Model",
                    "Cement Industry Best Practices"],
                "context_used": bool(context),
                "historical_context_available": len(self.context_window) > 0
            }

        except Exception as e:
            logger.error(f"Error answering query: {e}")
            import traceback
            traceback.print_exc()
            return {
                "answer": f"I encountered an error processing your query. Please try rephrasing or provide more context.",
                "confidence": 0.0,
                "sources": [],
                "error": str(e)
            }

    async def generate_optimization_plan(self,
                                         current_state: Dict[str, Any],
                                         target_metrics: Dict[str, Any],
                                         constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive optimization plan"""

        # Sanitize all inputs
        current_state = sanitize_for_json(current_state)
        target_metrics = sanitize_for_json(target_metrics)
        constraints = sanitize_for_json(constraints)

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


# Global service instance
gemini_service = EnhancedGeminiService()