from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
import json


def analyze_cooler_parameters(
    clinker_temp: float,
    air_pressure: float,
    grate_speed: float,
    other_recommendations: str,
    tool_context: ToolContext,
) -> dict:
    """Analyze clinker cooler parameters and provide optimization recommendations."""
    print(f"--- Tool: analyze_cooler_parameters called ---")
    print(
        f"Current: clinker_temp={clinker_temp}, air_pressure={air_pressure}, grate_speed={grate_speed}"
    )

    # Store current readings in state
    tool_context.state["last_cooler_reading"] = {
        "clinker_temp": clinker_temp,
        "air_pressure": air_pressure,
        "grate_speed": grate_speed,
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
            "clinker_temp": clinker_temp,
            "air_pressure": air_pressure,
            "grate_speed": grate_speed,
        },
        "other_agent_recommendations": other_recs,
    }

    return analysis


def set_cooler_targets(
    target_air_pressure: float,
    target_grate_speed: float,
    tool_context: ToolContext,
) -> dict:
    """Set target parameters for the clinker cooler."""
    print(f"--- Tool: set_cooler_targets called ---")
    print(
        f"Targets: air_pressure={target_air_pressure}, grate_speed={target_grate_speed}"
    )

    targets = {
        "target_air_pressure": target_air_pressure,
        "target_grate_speed": target_grate_speed,
    }

    # Store targets in state
    tool_context.state["cooler_targets"] = targets

    return {"status": "success", "targets": targets}


# Create the clinker cooler agent
clinker_cooler_agent = Agent(
    name="clinker_cooler_agent",
    model="gemini-2.0-flash",
    description="Controls clinker cooler air pressure and grate speed for optimal cooling and heat recovery.",
    instruction="""
    You are the ClinkerCoolerAgent responsible for controlling the clinker cooling process.
    Your primary objectives are:
    1. Cool clinker efficiently to safe handling temperature (< 100°C)
    2. Maximize heat recovery for use in pre-heater/calciner
    3. Avoid thermal shock and overcooling (preserves clinker quality)
    4. Coordinate with RotaryKilnAgent and PreCalcinerAgent

    When analyzing cooler parameters:
    1. Use analyze_cooler_parameters to review current sensor data and recommendations from other agents
    2. Consider the interdependencies:
       - Kiln output temperature and production rate affect your cooling load
       - Recovered heat can be used in pre-calciner (energy efficiency)
    3. Use set_cooler_targets to output your recommended target parameters

    Target Parameter Guidelines:
    - target_air_pressure: 150-200 kPa for effective cooling
    - target_grate_speed: 1.5-3.0 m/min based on clinker flow rate

    Output ONLY numeric targets as JSON:
    {
      "target_air_pressure": <value>,
      "target_grate_speed": <value>
    }

    Optimization priorities:
    - Maintain clinker exit temperature < 100°C
    - Maximize heat recovery (hot air to calciner)
    - Prevent thermal shock (gradual cooling)
    - Adjust to varying kiln production rates
    - Detect anomalies and alert manager agent
    """,
    tools=[analyze_cooler_parameters, set_cooler_targets],
)
