from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
import json
from google.adk.tools.agent_tool import AgentTool
from ..retriever_agent.agent import retriever_agent


def analyze_calciner_parameters(
    temperature: float,
    pressure: float,
    oxygen_level: float,
    co_level: float,
    nox_level: float,
    fuel_flow: float,
    feed_rate: float,
    tertiary_air_temp: float,
    calcination_degree: float,
    other_recommendations: str,
    tool_context: ToolContext,
) -> dict:
    """Analyze pre-calciner parameters and provide optimization recommendations."""
    print(f"--- Tool: analyze_calciner_parameters called ---")
    print(f"Temperature: {temperature}°C, Pressure: {pressure} mbar")
    print(f"O2: {oxygen_level}%, CO: {co_level}%, NOx: {nox_level} mg/Nm³")
    print(f"Fuel: {fuel_flow} t/h, Feed: {feed_rate} t/h")
    print(f"Tertiary Air: {tertiary_air_temp}°C, Calcination: {calcination_degree}%")

    # Store current readings in state
    tool_context.state["last_calciner_reading"] = {
        "temperature": temperature,
        "pressure": pressure,
        "oxygen_level": oxygen_level,
        "co_level": co_level,
        "nox_level": nox_level,
        "fuel_flow": fuel_flow,
        "feed_rate": feed_rate,
        "tertiary_air_temp": tertiary_air_temp,
        "calcination_degree": calcination_degree,
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
            "temperature": temperature,
            "pressure": pressure,
            "oxygen_level": oxygen_level,
            "co_level": co_level,
            "nox_level": nox_level,
            "fuel_flow": fuel_flow,
            "feed_rate": feed_rate,
            "tertiary_air_temp": tertiary_air_temp,
            "calcination_degree": calcination_degree,
        },
        "other_agent_recommendations": other_recs,
    }

    return analysis


def set_calciner_targets(
    targets_json: str,
    tool_context: ToolContext,
) -> dict:
    """Set target parameters for the pre-calciner. Accepts flexible JSON targets."""
    print(f"--- Tool: set_calciner_targets called ---")

    try:
        targets = json.loads(targets_json) if targets_json else {}
        print(f"Targets: {json.dumps(targets, indent=2)}")
    except:
        return {"status": "error", "message": "Failed to parse targets JSON"}

    # Store targets in state
    tool_context.state["calciner_targets"] = targets

    return {"status": "success", "targets": targets}


# Create the pre-calciner agent
pre_calciner_agent = Agent(
    name="pre_calciner_agent",
    model="gemini-2.0-flash",
    description="Controls the pre-calciner section, managing calcination process, emissions, and fuel efficiency.",
    instruction="""
    You are the PreCalcinerAgent responsible for managing the pre-calciner section.

    PRIMARY OBJECTIVES:
    1. Optimize calcination efficiency (convert CaCO3 to CaO)
    2. Maintain proper oxygen balance for complete combustion
    3. Minimize fuel consumption and emissions (CO, NOx)
    4. Coordinate with RotaryKilnAgent and ClinkerCoolerAgent
    5. Ensure optimal feed preparation for the kiln

    COMPREHENSIVE PARAMETERS TO ANALYZE (9 parameters):

    You receive ALL of the following parameters:
    - temperature: Current calciner temperature (Optimal: 820-900°C)
    - pressure: Calciner pressure (Optimal: -5 to -2 mbar)
    - oxygen_level: O2 concentration (Optimal: 2.0-4.0%)
    - co_level: Carbon monoxide level (Keep: 0-0.1%)
    - nox_level: Nitrogen oxide emissions (Keep: 0-800 mg/Nm³)
    - fuel_flow: Current fuel flow rate (Optimal: 8-12 t/h)
    - feed_rate: Material feed rate (Optimal: 250-350 t/h)
    - tertiary_air_temp: Tertiary air temperature from cooler (Optimal: 600-900°C)
    - calcination_degree: Degree of calcination achieved (Target: 85-95%)

    WHEN ANALYZING:
    1. Use analyze_calciner_parameters with ALL 9 parameters
    2. Review other agents' recommendations
    3. Consider manager's refined targets (if provided)
    4. Use retrieve_rag_documentation if you need to reference cement manufacturing best practices or technical documentation
    5. Analyze interdependencies:
       - Tertiary air temp from cooler affects fuel efficiency
       - Your calcination degree impacts kiln fuel consumption
       - O2 levels affect combustion efficiency system-wide
       - Pressure indicates draft stability
       - CO and NOx indicate combustion quality

    INTELLIGENT DECISION MAKING:
    **PRIMARY APPROACH**: Use retrieve_rag_documentation to query cement manufacturing best practices and optimization strategies. Ask questions like:
    - "What are optimal pre-calciner operating parameters?"
    - "How to optimize calcination degree and fuel efficiency?"
    - "Best practices for NOx and CO emissions reduction in calciners?"
    - "Optimal oxygen levels for calciner combustion?"
    - "Troubleshooting calciner pressure instability and draft issues?"

    Based on RAG documentation guidance:
    - Identify which parameters need adjustment
    - Decide which parameters are controllable vs. monitored
    - Determine optimal target values per documentation
    - Balance competing objectives (efficiency vs. emissions vs. quality)
    - Detect anomalies and apply documented solutions

    OUTPUT YOUR TARGETS:
    Use set_calciner_targets with a JSON string containing your recommended targets.
    Base your decisions on RAG documentation and current conditions.

    Example output format:
    {
      "target_temperature": 875,
      "target_fuel_flow": 9.5,
      "target_oxygen_level": 3.2,
      "target_feed_rate": 300,
      "optimization_notes": "Applied fuel reduction strategy from documentation: utilizing high tertiary air temp",
      "rag_references": "Pre-calciner Optimization Manual, Emission Control Guidelines"
    }

    **RAG-DRIVEN OPTIMIZATION**: Query documentation for optimization priorities instead of following hardcoded rules. The documentation will guide you on calcination targets, emission limits, and control strategies specific to your plant configuration.
    """,
    tools=[analyze_calciner_parameters, set_calciner_targets, AgentTool(retriever_agent)],
)
