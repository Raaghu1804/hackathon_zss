from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
import json
from google.adk.tools.agent_tool import AgentTool
# from ...tools.tools import root_agent
from ..retriever_agent.agent import retriever_agent




def analyze_cooler_parameters(
    inlet_temp: float,
    outlet_temp: float,
    secondary_air_temp: float,
    tertiary_air_temp: float,
    grate_speed: float,
    undergrate_pressure: float,
    cooling_air_flow: float,
    bed_height: float,
    cooler_efficiency: float,
    other_recommendations: str,
    tool_context: ToolContext,
) -> dict:
    """Analyze clinker cooler parameters and provide optimization recommendations."""
    print(f"--- Tool: analyze_cooler_parameters called ---")
    print(f"Inlet: {inlet_temp}°C, Outlet: {outlet_temp}°C")
    print(f"Secondary Air: {secondary_air_temp}°C, Tertiary Air: {tertiary_air_temp}°C")
    print(f"Grate Speed: {grate_speed} strokes/min, Pressure: {undergrate_pressure} mbar")
    print(f"Air Flow: {cooling_air_flow} kg/kg, Bed: {bed_height} mm, Efficiency: {cooler_efficiency}%")

    # Store current readings in state
    tool_context.state["last_cooler_reading"] = {
        "inlet_temp": inlet_temp,
        "outlet_temp": outlet_temp,
        "secondary_air_temp": secondary_air_temp,
        "tertiary_air_temp": tertiary_air_temp,
        "grate_speed": grate_speed,
        "undergrate_pressure": undergrate_pressure,
        "cooling_air_flow": cooling_air_flow,
        "bed_height": bed_height,
        "cooler_efficiency": cooler_efficiency,
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
            "inlet_temp": inlet_temp,
            "outlet_temp": outlet_temp,
            "secondary_air_temp": secondary_air_temp,
            "tertiary_air_temp": tertiary_air_temp,
            "grate_speed": grate_speed,
            "undergrate_pressure": undergrate_pressure,
            "cooling_air_flow": cooling_air_flow,
            "bed_height": bed_height,
            "cooler_efficiency": cooler_efficiency,
        },
        "other_agent_recommendations": other_recs,
    }

    return analysis


def set_cooler_targets(
    targets_json: str,
    tool_context: ToolContext,
) -> dict:
    """Set target parameters for the clinker cooler. Accepts flexible JSON targets."""
    print(f"--- Tool: set_cooler_targets called ---")

    try:
        targets = json.loads(targets_json) if targets_json else {}
        print(f"Targets: {json.dumps(targets, indent=2)}")
    except:
        return {"status": "error", "message": "Failed to parse targets JSON"}

    # Store targets in state
    tool_context.state["cooler_targets"] = targets

    return {"status": "success", "targets": targets}


# Create the clinker cooler agent
clinker_cooler_agent = Agent(
    name="clinker_cooler_agent",
    model="gemini-2.0-flash",
    description="Controls clinker cooler for optimal cooling, heat recovery, and energy efficiency.",
    instruction="""
    You are the ClinkerCoolerAgent responsible for controlling the clinker cooling process.

    PRIMARY OBJECTIVES:
    1. Cool clinker efficiently to safe handling temperature (100-150°C outlet)
    2. Maximize heat recovery (secondary and tertiary air to kiln/calciner)
    3. Prevent thermal shock (gradual cooling preserves clinker quality)
    4. Optimize cooler efficiency (75-85%)
    5. Coordinate with RotaryKilnAgent and PreCalcinerAgent

    COMPREHENSIVE PARAMETERS TO ANALYZE (9 parameters):

    You receive ALL of the following parameters:
    - inlet_temp: Clinker inlet temperature from kiln (Optimal: 1100-1300°C)
    - outlet_temp: Clinker outlet temperature (Optimal: 100-150°C)
    - secondary_air_temp: Hot air to kiln (Optimal: 600-1000°C)
    - tertiary_air_temp: Hot air to pre-calciner (Optimal: 600-900°C)
    - grate_speed: Grate movement rate (Optimal: 10-30 strokes/min)
    - undergrate_pressure: Air pressure under grate (Optimal: 40-80 mbar)
    - cooling_air_flow: Air-to-clinker ratio (Optimal: 2.3-3.3 kg/kg)
    - bed_height: Clinker bed depth (Optimal: 500-800 mm)
    - cooler_efficiency: Heat recovery efficiency (Target: 75-85%)

    WHEN ANALYZING:
    1. Use analyze_cooler_parameters with ALL 9 parameters
    2. Review other agents' recommendations
    3. Consider manager's refined targets (if provided)
    4. Use retrieve_rag_documentation if you need to reference cement manufacturing best practices or technical documentation
    5. Analyze interdependencies:
       - Inlet temp from kiln affects cooling load
       - Secondary air temp impacts kiln fuel efficiency
       - Tertiary air temp impacts calciner fuel efficiency
       - Grate speed affects bed height and cooling time
       - Undergrate pressure affects air distribution
       - Cooling air flow determines heat recovery vs. clinker cooling

    INTELLIGENT DECISION MAKING:
    **PRIMARY APPROACH**: Use retrieve_rag_documentation to query cement manufacturing best practices and optimization strategies. Ask questions like:
    - "What are optimal clinker cooler operating parameters?"
    - "How to maximize heat recovery in clinker coolers?"
    - "Best practices for cooler efficiency optimization"
    - "Troubleshooting high bed height in coolers"
    - "Optimal air flow strategies for cooling"

    Based on RAG documentation guidance:
    - Identify which parameters need adjustment
    - Decide which parameters are controllable vs. monitored
    - Determine optimal target values per documentation
    - Balance competing objectives (cooling vs. heat recovery)
    - Detect anomalies and apply documented solutions

    OUTPUT YOUR TARGETS:
    Use set_cooler_targets with a JSON string containing your recommended targets.
    Base your decisions on RAG documentation and current conditions.

    Example output format:
    {
      "target_grate_speed": 18,
      "target_cooling_air_flow": 2.8,
      "target_undergrate_pressure": 60,
      "target_secondary_air_temp": 850,
      "target_tertiary_air_temp": 780,
      "optimization_notes": "Applied strategy from documentation section 4.2: increased air flow for heat recovery",
      "rag_references": "Cooler Best Practices Manual, Heat Recovery Guidelines"
    }

    **RAG-DRIVEN OPTIMIZATION**: Query documentation for optimization priorities instead of following hardcoded rules. The documentation will guide you on parameters, targets, and control strategies specific to your plant configuration.
    """,
    tools=[analyze_cooler_parameters, set_cooler_targets, AgentTool(retriever_agent)],
)
