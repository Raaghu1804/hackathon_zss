from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
import json

def analyze_kiln_parameters(
    burning_zone_temp: float,
    back_end_temp: float,
    shell_temp: float,
    oxygen_level: float,
    nox_level: float,
    co_level: float,
    kiln_speed: float,
    fuel_rate: float,
    clinker_exit_temp: float,
    secondary_air_temp: float,
    other_recommendations: str,
    tool_context: ToolContext,
) -> dict:
    """Analyze rotary kiln parameters and provide optimization recommendations."""
    print(f"--- Tool: analyze_kiln_parameters called ---")
    print(f"Burning Zone: {burning_zone_temp}°C, Back End: {back_end_temp}°C, Shell: {shell_temp}°C")
    print(f"O2: {oxygen_level}%, CO: {co_level}%, NOx: {nox_level} mg/Nm³")
    print(f"Kiln Speed: {kiln_speed} rpm, Fuel: {fuel_rate} t/h")
    print(f"Clinker Exit: {clinker_exit_temp}°C, Secondary Air: {secondary_air_temp}°C")

    # Store current readings in state
    tool_context.state["last_kiln_reading"] = {
        "burning_zone_temp": burning_zone_temp,
        "back_end_temp": back_end_temp,
        "shell_temp": shell_temp,
        "oxygen_level": oxygen_level,
        "nox_level": nox_level,
        "co_level": co_level,
        "kiln_speed": kiln_speed,
        "fuel_rate": fuel_rate,
        "clinker_exit_temp": clinker_exit_temp,
        "secondary_air_temp": secondary_air_temp,
    }

    # Parse other recommendations if provided
    try:
        other_recs = json.loads(other_recommendations) if other_recommendations else {}
    except:
        other_recs = {}

    # Analysis with all comprehensive parameters
    analysis = {
        "status": "success",
        "current_readings": {
            "burning_zone_temp": burning_zone_temp,
            "back_end_temp": back_end_temp,
            "shell_temp": shell_temp,
            "oxygen_level": oxygen_level,
            "nox_level": nox_level,
            "co_level": co_level,
            "kiln_speed": kiln_speed,
            "fuel_rate": fuel_rate,
            "clinker_exit_temp": clinker_exit_temp,
            "secondary_air_temp": secondary_air_temp,
        },
        "other_agent_recommendations": other_recs,
    }

    return analysis


def set_kiln_targets(
    targets_json: str,
    tool_context: ToolContext,
) -> dict:
    """Set target parameters for the rotary kiln. Accepts flexible JSON targets."""
    print(f"--- Tool: set_kiln_targets called ---")

    try:
        targets = json.loads(targets_json) if targets_json else {}
        print(f"Targets: {json.dumps(targets, indent=2)}")
    except:
        return {"status": "error", "message": "Failed to parse targets JSON"}

    # Store targets in state
    tool_context.state["kiln_targets"] = targets

    return {"status": "success", "targets": targets}


# Create the rotary kiln agent
rotary_kiln_agent = Agent(
    name="rotary_kiln_agent",
    model="gemini-2.0-flash",
    description="Controls rotary kiln for clinker production, optimizing temperature profiles, emissions, and energy efficiency.",
    instruction="""
    You are the RotaryKilnAgent responsible for controlling the rotary kiln in the burning zone.

    PRIMARY OBJECTIVES:
    1. Maintain optimal clinker quality (C3S, C2S ratios)
    2. Maximize energy efficiency
    3. Minimize emissions (CO, NOx)
    4. Ensure stable operation
    5. Coordinate with PreCalcinerAgent and ClinkerCoolerAgent

    COMPREHENSIVE PARAMETERS TO ANALYZE (10 parameters):

    You receive ALL of the following parameters:
    - burning_zone_temp: Temperature in the burning zone (Optimal: 1400-1500°C)
    - back_end_temp: Back-end temperature (Optimal: 800-1200°C)
    - shell_temp: Shell surface temperature (Optimal: 200-350°C)
    - oxygen_level: O2 concentration in kiln (Optimal: 1.0-3.0%)
    - nox_level: Nitrogen oxide emissions (Keep: 0-1200 mg/Nm³)
    - co_level: Carbon monoxide level (Keep: 0-0.05%)
    - kiln_speed: Rotation speed (Optimal: 3.0-5.0 rpm)
    - fuel_rate: Current fuel consumption (Optimal: 10-15 t/h)
    - clinker_exit_temp: Clinker temperature leaving kiln (Optimal: 1100-1300°C)
    - secondary_air_temp: Secondary air temperature from cooler (Optimal: 600-1000°C)

    WHEN ANALYZING:
    1. Use analyze_kiln_parameters with ALL 10 parameters
    2. Review other agents' recommendations
    3. Consider manager's refined targets (if provided)
    4. Analyze interdependencies:
       - Pre-calciner's calcination degree affects fuel needs
       - Secondary air temp from cooler impacts fuel efficiency
       - Clinker exit temp affects cooler load
       - Back-end temp indicates pre-heater/calciner performance
       - Shell temp indicates refractory condition and heat loss
       - O2, CO, NOx levels indicate combustion efficiency

    INTELLIGENT DECISION MAKING:
    Use your knowledge of cement manufacturing best practices and optimization strategies to:
    - Identify which parameters need adjustment
    - Decide which parameters are controllable vs. monitored
    - Determine optimal target values based on standard industry practices
    - Balance competing objectives (quality vs. efficiency vs. emissions)
    - Detect coating buildup (shell temp patterns)
    - Identify combustion issues (O2, CO patterns)

    Key considerations:
    - Optimal burning zone temperature depends on clinker chemistry and quality requirements
    - High CO indicates incomplete combustion - increase O2 or adjust fuel
    - High NOx indicates excessive temperatures - reduce burning zone temp or optimize combustion
    - Shell temperature patterns reveal refractory coating condition
    - Secondary air temperature from cooler reduces fuel requirements

    OUTPUT YOUR TARGETS:
    Use set_kiln_targets with a JSON string containing your recommended targets.
    Base your decisions on cement industry best practices and current conditions.

    Example output format:
    {
      "target_burning_zone_temp": 1450,
      "target_fuel_rate": 12.5,
      "target_kiln_speed": 3.8,
      "target_oxygen_level": 2.0,
      "optimization_notes": "Reduced fuel rate due to high secondary air temp from cooler, maintaining optimal burning zone temperature"
    }
    """,
    tools=[analyze_kiln_parameters, set_kiln_targets],
)
