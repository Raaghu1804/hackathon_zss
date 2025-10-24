from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
import json


def analyze_kiln_parameters(
    kiln_temp: float,
    feed_rate: float,
    fuel_rate: float,
    other_recommendations: str,
    tool_context: ToolContext,
) -> dict:
    """Analyze rotary kiln parameters and provide optimization recommendations."""
    print(f"--- Tool: analyze_kiln_parameters called ---")
    print(f"Current: temp={kiln_temp}, feed={feed_rate}, fuel={fuel_rate}")

    # Store current readings in state
    tool_context.state["last_kiln_reading"] = {
        "kiln_temp": kiln_temp,
        "feed_rate": feed_rate,
        "fuel_rate": fuel_rate,
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
            "kiln_temp": kiln_temp,
            "feed_rate": feed_rate,
            "fuel_rate": fuel_rate,
        },
        "other_agent_recommendations": other_recs,
    }

    return analysis


def set_kiln_targets(
    target_kiln_temp: float,
    target_fuel_rate: float,
    target_rotation_speed: float,
    tool_context: ToolContext,
) -> dict:
    """Set target parameters for the rotary kiln."""
    print(f"--- Tool: set_kiln_targets called ---")
    print(
        f"Targets: temp={target_kiln_temp}, fuel={target_fuel_rate}, rotation={target_rotation_speed}"
    )

    targets = {
        "target_kiln_temp": target_kiln_temp,
        "target_fuel_rate": target_fuel_rate,
        "target_rotation_speed": target_rotation_speed,
    }

    # Store targets in state
    tool_context.state["kiln_targets"] = targets

    return {"status": "success", "targets": targets}


# Create the rotary kiln agent
rotary_kiln_agent = Agent(
    name="rotary_kiln_agent",
    model="gemini-2.0-flash",
    description="Controls rotary kiln for clinker production, optimizing temperature, fuel rate, and rotation speed.",
    instruction="""
    You are the RotaryKilnAgent responsible for controlling the rotary kiln in the burning zone.
    Your primary objectives are:
    1. Maintain optimal clinker quality
    2. Maximize energy efficiency
    3. Coordinate with other agents (PreCalcinerAgent and ClinkerCoolerAgent)

    When analyzing kiln parameters:
    1. Use analyze_kiln_parameters to review current sensor data and recommendations from other agents
    2. Consider the interdependencies:
       - Pre-calciner outputs affect your feed quality
       - Your output temperature affects cooler operations
    3. Use set_kiln_targets to output your recommended target parameters

    Target Parameter Guidelines:
    - target_kiln_temp: Optimal range 1400-1500°C (clinker formation zone)
    - target_fuel_rate: Adjust based on feed rate and desired temperature
    - target_rotation_speed: Typically 2.5-4.0 RPM for optimal residence time

    Output ONLY numeric targets as JSON:
    {
      "target_kiln_temp": <value>,
      "target_fuel_rate": <value>,
      "target_rotation_speed": <value>
    }

    Optimization priorities:
    - Reduce fuel consumption while maintaining quality
    - Respond to pre-calciner temperature changes
    - Coordinate with cooler for heat recovery
    - Detect anomalies and alert manager agent
    """,
    tools=[analyze_kiln_parameters, set_kiln_targets],
)
