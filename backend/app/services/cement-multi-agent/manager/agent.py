from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.tool_context import ToolContext
import json

from .sub_agents.rotary_kiln_agent.agent import rotary_kiln_agent
from .sub_agents.clinker_cooler_agent.agent import clinker_cooler_agent
from .sub_agents.pre_calciner_agent.agent import pre_calciner_agent
from .tools.tools import get_current_time


def review_all_agent_outputs(
    kiln_targets: str,
    calciner_targets: str,
    cooler_targets: str,
    tool_context: ToolContext,
) -> dict:
    """Review outputs from all specialist agents and identify conflicts or optimization opportunities."""
    print("--- Tool: review_all_agent_outputs called ---")

    try:
        kiln = json.loads(kiln_targets) if kiln_targets else {}
        calciner = json.loads(calciner_targets) if calciner_targets else {}
        cooler = json.loads(cooler_targets) if cooler_targets else {}
    except:
        return {
            "status": "error",
            "message": "Failed to parse agent outputs",
        }

    # Store all targets for reference
    tool_context.state["all_targets"] = {
        "kiln": kiln,
        "calciner": calciner,
        "cooler": cooler,
    }

    return {
        "status": "success",
        "kiln_targets": kiln,
        "calciner_targets": calciner,
        "cooler_targets": cooler,
    }


def issue_refined_targets(
    refined_kiln_temp: float,
    refined_fuel_rate: float,
    refined_rotation_speed: float,
    refined_calciner_temp: float,
    refined_o2_concentration: float,
    refined_fuel_flow: float,
    refined_air_pressure: float,
    refined_grate_speed: float,
    tool_context: ToolContext,
) -> dict:
    """Issue refined and balanced targets to all agents after supervision."""
    print("--- Tool: issue_refined_targets called ---")

    refined_targets = {
        "rotary_kiln": {
            "target_kiln_temp": refined_kiln_temp,
            "target_fuel_rate": refined_fuel_rate,
            "target_rotation_speed": refined_rotation_speed,
        },
        "pre_calciner": {
            "target_calciner_temp": refined_calciner_temp,
            "target_o2_concentration": refined_o2_concentration,
            "target_fuel_flow": refined_fuel_flow,
        },
        "clinker_cooler": {
            "target_air_pressure": refined_air_pressure,
            "target_grate_speed": refined_grate_speed,
        },
    }

    # Store refined targets in state
    tool_context.state["refined_targets"] = refined_targets

    print(f"Refined targets issued: {json.dumps(refined_targets, indent=2)}")

    return {"status": "success", "refined_targets": refined_targets}


def detect_system_anomalies(
    sensor_data: str,
    tool_context: ToolContext,
) -> dict:
    """Detect anomalies across the entire clinkerization system."""
    print("--- Tool: detect_system_anomalies called ---")

    try:
        sensors = json.loads(sensor_data) if sensor_data else {}
    except:
        return {"status": "error", "message": "Failed to parse sensor data"}

    anomalies = []

    # Basic anomaly detection logic (can be enhanced)
    kiln_data = sensors.get("rotary_kiln", {})
    if kiln_data.get("kiln_temp", 0) > 1550:
        anomalies.append("CRITICAL: Kiln temperature exceeds safe limit (>1550°C)")
    elif kiln_data.get("kiln_temp", 0) < 1350:
        anomalies.append("WARNING: Kiln temperature too low for optimal clinker quality")

    calciner_data = sensors.get("pre_calciner", {})
    if calciner_data.get("o2_concentration", 0) > 7:
        anomalies.append("WARNING: Excess oxygen in calciner (fuel inefficiency)")
    elif calciner_data.get("o2_concentration", 0) < 2:
        anomalies.append("CRITICAL: Low oxygen - incomplete combustion risk")

    cooler_data = sensors.get("clinker_cooler", {})
    if cooler_data.get("clinker_temp", 0) > 350:
        anomalies.append("WARNING: Clinker exit temperature high (heat recovery issue)")

    tool_context.state["detected_anomalies"] = anomalies

    return {
        "status": "success",
        "anomaly_count": len(anomalies),
        "anomalies": anomalies,
    }


# Create the manager agent (supervisor)
root_agent = Agent(
    name="manager",
    model="gemini-2.0-flash",
    description="Supervisor manager agent for cement plant clinkerization process",
    instruction="""
    You are the ManagerAgent - the supervisor overseeing the entire cement clinkerization process.

    Your PRIMARY responsibilities:
    1. **Supervise all specialist agents**: RotaryKilnAgent, PreCalcinerAgent, ClinkerCoolerAgent
    2. **Detect system-wide anomalies** using detect_system_anomalies tool
    3. **Review and balance** all agent outputs using review_all_agent_outputs
    4. **Issue refined targets** that optimize the ENTIRE system (not just individual units)
    5. **Ensure coordination** between all units for maximum efficiency

    WORKFLOW:
    1. Collect sensor data from all units (rotary_kiln, pre_calciner, clinker_cooler)
    2. Use detect_system_anomalies to identify any critical issues
    3. Delegate to specialist agents to get their initial recommendations
    4. Use review_all_agent_outputs to analyze all recommendations together
    5. Balance the targets considering:
       - Energy efficiency (minimize total fuel consumption)
       - Clinker quality (maintain proper chemistry and strength)
       - System stability (avoid oscillations)
       - Safety limits (temperature, pressure constraints)
    6. Use issue_refined_targets to output final balanced parameters

    SUPERVISION PRIORITIES:
    - **Energy optimization**: Minimize combined fuel usage across kiln + calciner
    - **Heat recovery**: Ensure cooler heat is utilized by calciner/pre-heater
    - **Quality maintenance**: Keep clinker within spec (C3S, C2S ratios)
    - **Conflict resolution**: When agents have competing goals, find optimal balance
    - **Anomaly response**: Override agent recommendations if safety risk detected

    OUTPUT FORMAT (use issue_refined_targets):
    {
      "refined_kiln_temp": <value>,
      "refined_fuel_rate": <value>,
      "refined_rotation_speed": <value>,
      "refined_calciner_temp": <value>,
      "refined_o2_concentration": <value>,
      "refined_fuel_flow": <value>,
      "refined_air_pressure": <value>,
      "refined_grate_speed": <value>
    }

    You are the ultimate decision-maker. Always consider the WHOLE SYSTEM, not individual units.
    Delegate analysis to specialist agents, but YOU make the final balanced decisions.
    """,
    sub_agents=[rotary_kiln_agent, clinker_cooler_agent, pre_calciner_agent],
    tools=[
        review_all_agent_outputs,
        issue_refined_targets,
        detect_system_anomalies,
        get_current_time,
    ],
)
