from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
import json


def analyze_calciner_parameters(
    calciner_temp: float,
    o2_concentration: float,
    fuel_flow: float,
    other_recommendations: str,
    tool_context: ToolContext,
) -> dict:
    """Analyze pre-calciner parameters and provide optimization recommendations."""
    print(f"--- Tool: analyze_calciner_parameters called ---")
    print(
        f"Current: temp={calciner_temp}, O2={o2_concentration}%, fuel={fuel_flow}"
    )

    # Store current readings in state
    tool_context.state["last_calciner_reading"] = {
        "calciner_temp": calciner_temp,
        "o2_concentration": o2_concentration,
        "fuel_flow": fuel_flow,
    }

    # Parse other recommendations if provided
    try:
        other_recs = json.loads(other_recommendations) if other_recommendations else {}
    except:
        other_recs = {}

    # Basic analysis logic
    analysis = {
        "status": "success",
        "current_readings": {
            "calciner_temp": calciner_temp,
            "o2_concentration": o2_concentration,
            "fuel_flow": fuel_flow,
        },
        "other_agent_recommendations": other_recs,
    }

    return analysis


def set_calciner_targets(
    target_calciner_temp: float,
    target_o2_concentration: float,
    target_fuel_flow: float,
    tool_context: ToolContext,
) -> dict:
    """Set target parameters for the pre-calciner."""
    print(f"--- Tool: set_calciner_targets called ---")
    print(
        f"Targets: temp={target_calciner_temp}, O2={target_o2_concentration}%, fuel={target_fuel_flow}"
    )

    targets = {
        "target_calciner_temp": target_calciner_temp,
        "target_o2_concentration": target_o2_concentration,
        "target_fuel_flow": target_fuel_flow,
    }

    # Store targets in state
    tool_context.state["calciner_targets"] = targets

    return {"status": "success", "targets": targets}


# Create the pre-calciner agent
pre_calciner_agent = Agent(
    name="pre_calciner_agent",
    model="gemini-2.0-flash",
    description="Controls the pre-calciner section, managing calcination process and oxygen balance for optimal fuel efficiency.",
    instruction="""
    You are the PreCalcinerAgent responsible for managing the pre-calciner section.
    Your primary objectives are:
    1. Optimize calcination efficiency (convert CaCO3 to CaO)
    2. Maintain proper oxygen concentration for complete combustion
    3. Minimize fuel consumption
    4. Coordinate with RotaryKilnAgent and ClinkerCoolerAgent

    When analyzing calciner parameters:
    1. Use analyze_calciner_parameters to review current sensor data and recommendations from other agents
    2. Consider the interdependencies:
       - Your output temperature and calcination degree affect kiln performance
       - O2 levels impact fuel efficiency across the system
    3. Use set_calciner_targets to output your recommended target parameters

    Target Parameter Guidelines:
    - target_calciner_temp: Optimal range 850-950°C (calcination zone)
    - target_o2_concentration: 3-6% for efficient combustion
    - target_fuel_flow: Adjust based on feed rate and target temperature

    Output ONLY numeric targets as JSON:
    {
      "target_calciner_temp": <value>,
      "target_o2_concentration": <value>,
      "target_fuel_flow": <value>
    }

    Optimization priorities:
    - Achieve 85-95% calcination before material enters kiln
    - Minimize excess oxygen (reduces heat loss)
    - Balance fuel flow for stable temperature
    - Coordinate with kiln agent for feed quality
    - Detect anomalies and alert manager agent
    """,
    tools=[analyze_calciner_parameters, set_calciner_targets],
)
