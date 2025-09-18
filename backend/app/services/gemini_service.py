# backend/app/services/gemini_service.py

import google.generativeai as genai
from typing import Dict, Any, Optional
from app.config import settings
import json

class GeminiService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
    async def analyze_sensor_data(self, unit: str, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sensor data using Gemini AI"""
        
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
        
        try:
            response = self.model.generate_content(prompt)
            # Parse the JSON response
            result_text = response.text.strip()
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]
            
            return json.loads(result_text.strip())
        except Exception as e:
            print(f"Error in Gemini analysis: {e}")
            return {
                "status": "error",
                "health_score": 0,
                "efficiency_score": 0,
                "issues": ["AI analysis failed"],
                "recommendations": [],
                "optimization_opportunities": []
            }
    
    async def generate_agent_communication(
        self, 
        from_agent: str, 
        to_agent: str, 
        context: Dict[str, Any]
    ) -> str:
        """Generate agent-to-agent communication"""
        
        prompt = f"""
        You are the {from_agent} AI agent communicating with the {to_agent} AI agent.
        Based on the following context, generate a professional communication message:
        
        Context: {json.dumps(context, indent=2)}
        
        The message should be technical, specific, and action-oriented.
        Focus on operational parameters and optimization opportunities.
        Keep the message concise (2-3 sentences).
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error generating communication: {e}")
            return f"Error in generating communication: {str(e)}"
    
    async def suggest_optimization(
        self, 
        unit: str, 
        current_params: Dict[str, float],
        issue: str
    ) -> Dict[str, Any]:
        """Suggest parameter optimizations"""
        
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
        
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]
            
            return json.loads(result_text.strip())
        except Exception as e:
            print(f"Error in optimization suggestion: {e}")
            return {
                "adjustments": {},
                "expected_benefits": [],
                "risks": ["Unable to generate optimization"],
                "implementation_steps": []
            }
    
    async def answer_analytics_query(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Answer user queries about the cement plant operations"""
        
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
        
        try:
            response = self.model.generate_content(prompt)
            return {
                "answer": response.text.strip(),
                "confidence": 0.95,
                "sources": ["Gemini AI Model", "Cement Industry Best Practices"]
            }
        except Exception as e:
            print(f"Error answering query: {e}")
            return {
                "answer": f"Error processing query: {str(e)}",
                "confidence": 0.0,
                "sources": []
            }

# Global Gemini service instance
gemini_service = GeminiService()