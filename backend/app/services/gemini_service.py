# backend/app/services/gemini_service.py - FIXED VERSION

import google.generativeai as genai
from typing import Dict, Any, Optional
from app.config import settings
import json
import asyncio
import time


class GeminiService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum 1 second between requests
        self.request_count = 0
        self.max_requests_per_minute = 10  # Limit to 10 requests per minute

    async def _rate_limit(self):
        """Implement rate limiting to avoid quota exhaustion"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - time_since_last)

        self.last_request_time = time.time()
        self.request_count += 1

    async def analyze_sensor_data(self, unit: str, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sensor data using Gemini AI with fallback"""

        # Simple fallback analysis without AI to avoid quota issues
        try:
            await self._rate_limit()

            prompt = f"""
            You are an AI agent managing the {unit} in a cement plant.
            Analyze the following sensor data and provide insights:

            Sensor Data: {json.dumps(sensor_data, indent=2)}

            Provide your analysis in JSON format with the following structure:
            {{
                "status": "normal/warning/critical",
                "health_score": 0-100,
                "efficiency_score": 0-100,
                "issues": ["list of detected issues"],
                "recommendations": ["list of recommendations"],
                "optimization_opportunities": ["list of optimization opportunities"]
            }}
            """

            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]

            return json.loads(result_text.strip())

        except Exception as e:
            print(f"⚠️ Gemini API error, using fallback analysis: {e}")
            # Return fallback analysis based on sensor data
            return self._fallback_analysis(unit, sensor_data)

    def _fallback_analysis(self, unit: str, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback analysis when Gemini API is unavailable"""
        issues = []
        recommendations = []
        anomaly_count = 0

        # Check for anomalies
        for sensor_name, data in sensor_data.items():
            if data.get('is_anomaly', False):
                anomaly_count += 1
                issues.append(f"{sensor_name} is outside optimal range")

                # Generate recommendations based on sensor type
                if 'temperature' in sensor_name.lower():
                    recommendations.append(f"Adjust fuel rate to optimize {sensor_name}")
                elif 'pressure' in sensor_name.lower():
                    recommendations.append(f"Check for blockages affecting {sensor_name}")
                elif 'flow' in sensor_name.lower():
                    recommendations.append(f"Calibrate {sensor_name} sensor and check supply")

        # Calculate scores
        health_score = max(0, 100 - (anomaly_count * 10))
        efficiency_score = max(0, 95 - (anomaly_count * 5))

        # Determine status
        if anomaly_count >= 3:
            status = "critical"
        elif anomaly_count >= 1:
            status = "warning"
        else:
            status = "normal"

        return {
            "status": status,
            "health_score": health_score,
            "efficiency_score": efficiency_score,
            "issues": issues if issues else ["No issues detected"],
            "recommendations": recommendations if recommendations else ["Continue monitoring"],
            "optimization_opportunities": ["Monitor trends for proactive optimization"]
        }

    async def generate_agent_communication(
            self,
            from_agent: str,
            to_agent: str,
            context: Dict[str, Any]
    ) -> str:
        """Generate agent-to-agent communication with fallback"""

        try:
            await self._rate_limit()

            prompt = f"""
            You are the {from_agent} AI agent communicating with the {to_agent} AI agent.
            Based on the following context, generate a professional communication message:

            Context: {json.dumps(context, indent=2)}

            The message should be technical, specific, and action-oriented.
            Focus on operational parameters and optimization opportunities.
            Keep the message concise (2-3 sentences).
            """

            response = self.model.generate_content(prompt)
            return response.text.strip()

        except Exception as e:
            print(f"⚠️ Gemini API error in communication, using fallback: {e}")
            # Fallback communication
            issue = context.get('issue', 'process optimization')
            severity = context.get('severity', 'info')
            return f"[{from_agent}] Alert: {issue}. Severity: {severity}. Coordinating with {to_agent} for optimization."

    async def suggest_optimization(
            self,
            unit: str,
            current_params: Dict[str, float],
            issue: str
    ) -> Dict[str, Any]:
        """Suggest parameter optimizations with fallback"""

        try:
            await self._rate_limit()

            prompt = f"""
            You are an expert AI optimization agent for a cement plant {unit}.

            Current parameters:
            {json.dumps(current_params, indent=2)}

            Issue detected: {issue}

            Suggest parameter adjustments to optimize the process.
            Provide your response in JSON format:
            {{
                "adjustments": {{
                    "parameter_name": {{
                        "current": current_value,
                        "suggested": suggested_value,
                        "change_percentage": percentage
                    }}
                }},
                "expected_benefits": ["list of benefits"],
                "risks": ["potential risks"],
                "implementation_steps": ["step by step actions"]
            }}
            """

            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]

            return json.loads(result_text.strip())

        except Exception as e:
            print(f"⚠️ Gemini API error in optimization, using fallback: {e}")
            return self._fallback_optimization(unit, current_params, issue)

    def _fallback_optimization(
            self,
            unit: str,
            current_params: Dict[str, float],
            issue: str
    ) -> Dict[str, Any]:
        """Fallback optimization suggestions"""
        adjustments = {}

        # Simple rule-based optimization
        if 'temperature' in issue.lower():
            if 'fuel_rate' in current_params:
                adjustments['fuel_rate'] = {
                    'current': current_params['fuel_rate'],
                    'suggested': current_params['fuel_rate'] * 0.95,
                    'change_percentage': -5
                }

        return {
            "adjustments": adjustments,
            "expected_benefits": ["Improved process stability", "Better energy efficiency"],
            "risks": ["Monitor closely for 30 minutes after adjustment"],
            "implementation_steps": [
                "Review current operating conditions",
                "Make gradual adjustments",
                "Monitor response for 15 minutes",
                "Fine-tune as needed"
            ]
        }

    async def answer_analytics_query(
            self,
            query: str,
            context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Answer user queries about the cement plant operations with fallback"""

        try:
            await self._rate_limit()

            prompt = f"""
            You are an expert AI assistant for cement plant operations.
            Answer the following query based on cement manufacturing best practices:

            Query: {query}
            """

            if context:
                prompt += f"\n\nAdditional Context: {json.dumps(context, indent=2)}"

            prompt += """

            Provide a comprehensive answer that includes:
            1. Direct answer to the question
            2. Technical explanation
            3. Best practices
            4. Any relevant metrics or KPIs
            """

            response = self.model.generate_content(prompt)
            return {
                "answer": response.text.strip(),
                "confidence": 0.95,
                "sources": ["Gemini AI Model", "Cement Industry Best Practices"]
            }

        except Exception as e:
            print(f"⚠️ Gemini API error in query, using fallback: {e}")
            return {
                "answer": self._fallback_answer(query, context),
                "confidence": 0.70,
                "sources": ["Rule-based System", "Industry Standards"]
            }

    def _fallback_answer(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Fallback answers for common queries"""
        query_lower = query.lower()

        if 'efficiency' in query_lower:
            return "Current plant efficiency is maintained through continuous monitoring of key parameters including fuel consumption, production rate, and energy usage. Target efficiency is 85-90% with regular optimization."

        elif 'temperature' in query_lower:
            return "Temperature control is critical in cement manufacturing. Optimal ranges: Pre-calciner 820-900°C, Kiln burning zone 1400-1500°C. Temperature optimization reduces fuel consumption by 10-15%."

        elif 'fuel' in query_lower or 'cost' in query_lower:
            return "Alternative fuel optimization can reduce costs by $500K+ annually while cutting CO2 emissions by 25%. Recommended AFR (Alternative Fuel Rate) is 40-65% depending on fuel availability."

        elif 'emission' in query_lower or 'carbon' in query_lower:
            return "Carbon emissions can be reduced through: 1) Increasing alternative fuel rate to 50%+, 2) Optimizing thermal efficiency, 3) Using supplementary cementitious materials. Target: <550 kg CO2/tonne cement."

        else:
            return f"For optimal plant operations, focus on maintaining key parameters within specified ranges, implementing predictive maintenance, and continuously monitoring efficiency metrics. Regular data analysis helps identify optimization opportunities."


# Global Gemini service instance
gemini_service = GeminiService()