from google.adk.agents import Agent
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
    """Detect anomalies across the entire clinkerization system with all comprehensive parameters."""
    print("--- Tool: detect_system_anomalies called ---")

    try:
        sensors = json.loads(sensor_data) if sensor_data else {}
    except:
        return {"status": "error", "message": "Failed to parse sensor data"}

    anomalies = []

    # ROTARY KILN Anomaly Detection (10 parameters)
    kiln_data = sensors.get("rotary_kiln", {})
    if kiln_data.get("burning_zone_temp", 0) > 1500:
        anomalies.append("CRITICAL: Kiln burning zone temp exceeds safe limit (>1500°C)")
    elif kiln_data.get("burning_zone_temp", 0) < 1400:
        anomalies.append("WARNING: Kiln burning zone temp too low (<1400°C)")

    if kiln_data.get("back_end_temp", 0) > 1200:
        anomalies.append("WARNING: Kiln back-end temp too high (>1200°C)")
    elif kiln_data.get("back_end_temp", 0) < 800:
        anomalies.append("WARNING: Kiln back-end temp too low (<800°C)")

    if kiln_data.get("shell_temp", 0) > 350:
        anomalies.append("WARNING: Kiln shell temp high - possible coating loss (>350°C)")
    elif kiln_data.get("shell_temp", 0) < 200:
        anomalies.append("INFO: Kiln shell temp low (<200°C)")

    if kiln_data.get("oxygen_level", 0) > 3.0:
        anomalies.append("WARNING: Excess O2 in kiln - fuel inefficiency (>3%)")
    elif kiln_data.get("oxygen_level", 0) < 1.0:
        anomalies.append("CRITICAL: Low O2 in kiln - incomplete combustion (<1%)")

    if kiln_data.get("co_level", 0) > 0.05:
        anomalies.append("CRITICAL: High CO in kiln - incomplete combustion (>0.05%)")

    if kiln_data.get("nox_level", 0) > 1200:
        anomalies.append("WARNING: High NOx emissions from kiln (>1200 mg/Nm³)")

    # PRE-CALCINER Anomaly Detection (9 parameters)
    calciner_data = sensors.get("pre_calciner", {})
    if calciner_data.get("temperature", 0) > 900:
        anomalies.append("WARNING: Calciner temp too high (>900°C)")
    elif calciner_data.get("temperature", 0) < 820:
        anomalies.append("WARNING: Calciner temp too low (<820°C)")

    if calciner_data.get("pressure", 0) > -2:
        anomalies.append("WARNING: Calciner pressure high (draft issue)")
    elif calciner_data.get("pressure", 0) < -5:
        anomalies.append("WARNING: Calciner pressure too low (excessive draft)")

    if calciner_data.get("oxygen_level", 0) > 4.0:
        anomalies.append("WARNING: Excess O2 in calciner (>4%)")
    elif calciner_data.get("oxygen_level", 0) < 2.0:
        anomalies.append("CRITICAL: Low O2 in calciner (<2%)")

    if calciner_data.get("co_level", 0) > 0.1:
        anomalies.append("CRITICAL: High CO in calciner (>0.1%)")

    if calciner_data.get("nox_level", 0) > 800:
        anomalies.append("WARNING: High NOx from calciner (>800 mg/Nm³)")

    if calciner_data.get("calcination_degree", 0) < 85:
        anomalies.append("WARNING: Low calcination degree (<85%)")
    elif calciner_data.get("calcination_degree", 0) > 95:
        anomalies.append("INFO: Very high calcination degree (>95%)")

    # CLINKER COOLER Anomaly Detection (9 parameters)
    cooler_data = sensors.get("clinker_cooler", {})
    if cooler_data.get("inlet_temp", 0) > 1300:
        anomalies.append("WARNING: Cooler inlet temp high (>1300°C)")
    elif cooler_data.get("inlet_temp", 0) < 1100:
        anomalies.append("WARNING: Cooler inlet temp low (<1100°C)")

    if cooler_data.get("outlet_temp", 0) > 150:
        anomalies.append("WARNING: Cooler outlet temp high (>150°C)")
    elif cooler_data.get("outlet_temp", 0) < 100:
        anomalies.append("INFO: Cooler outlet temp very low (<100°C)")

    if cooler_data.get("secondary_air_temp", 0) < 600:
        anomalies.append("WARNING: Low secondary air temp - poor heat recovery (<600°C)")

    if cooler_data.get("tertiary_air_temp", 0) < 600:
        anomalies.append("WARNING: Low tertiary air temp - poor heat recovery (<600°C)")

    if cooler_data.get("cooler_efficiency", 0) < 75:
        anomalies.append("WARNING: Low cooler efficiency (<75%)")

    if cooler_data.get("bed_height", 0) > 800:
        anomalies.append("WARNING: High bed height - possible accumulation (>800 mm)")
    elif cooler_data.get("bed_height", 0) < 500:
        anomalies.append("WARNING: Low bed height (<500 mm)")

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
    description="Supervisor manager agent for cement plant clinkerization process with comprehensive parameter monitoring",
    instruction="""
    You are the ManagerAgent - the supervisor overseeing the entire cement clinkerization process.

    YOUR PRIMARY RESPONSIBILITIES:
    1. **Supervise all specialist agents**: RotaryKilnAgent, PreCalcinerAgent, ClinkerCoolerAgent
    2. **Monitor 28 comprehensive parameters** across all three units
    3. **Detect system-wide anomalies** using detect_system_anomalies tool
    4. **Review and balance** all agent outputs using review_all_agent_outputs
    5. **Issue refined targets** that optimize the ENTIRE system
    6. **Ensure coordination** and heat/material flow between units

    COMPREHENSIVE SYSTEM PARAMETERS YOU MONITOR:

    **ROTARY KILN (10 parameters):**
    - burning_zone_temp (1400-1500°C)
    - back_end_temp (800-1200°C)
    - shell_temp (200-350°C)
    - oxygen_level (1.0-3.0%)
    - nox_level (0-1200 mg/Nm³)
    - co_level (0-0.05%)
    - kiln_speed (3.0-5.0 rpm)
    - fuel_rate (10-15 t/h)
    - clinker_exit_temp (1100-1300°C)
    - secondary_air_temp (600-1000°C)

    **PRE-CALCINER (9 parameters):**
    - temperature (820-900°C)
    - pressure (-5 to -2 mbar)
    - oxygen_level (2.0-4.0%)
    - co_level (0-0.1%)
    - nox_level (0-800 mg/Nm³)
    - fuel_flow (8-12 t/h)
    - feed_rate (250-350 t/h)
    - tertiary_air_temp (600-900°C)
    - calcination_degree (85-95%)

    **CLINKER COOLER (9 parameters):**
    - inlet_temp (1100-1300°C)
    - outlet_temp (100-150°C)
    - secondary_air_temp (600-1000°C)
    - tertiary_air_temp (600-900°C)
    - grate_speed (10-30 strokes/min)
    - undergrate_pressure (40-80 mbar)
    - cooling_air_flow (2.3-3.3 kg/kg)
    - bed_height (500-800 mm)
    - cooler_efficiency (75-85%)

    WORKFLOW:
    1. Collect sensor data from all units (28 total parameters)
    2. Delegate to specialist agents for detailed analysis and anomaly detection
    3. Use review_all_agent_outputs to analyze recommendations from all specialist agents
    4. Balance targets considering:
       - **Energy**: Minimize total fuel (kiln + calciner)
       - **Emissions**: Minimize CO and NOx system-wide
       - **Heat recovery**: Maximize secondary/tertiary air temps
       - **Quality**: Maintain calcination degree and clinker chemistry
       - **Stability**: Avoid pressure/temperature oscillations
       - **Safety**: Enforce all parameter limits
    5. Use issue_refined_targets with flexible JSON output to provide final balanced targets

    SYSTEM INTERDEPENDENCIES TO CONSIDER:
    - Tertiary air temp from cooler → reduces calciner fuel need
    - Secondary air temp from cooler → reduces kiln fuel need
    - Calcination degree from calciner → affects kiln fuel need
    - Kiln clinker exit temp → affects cooler inlet load
    - Calciner pressure → indicates draft stability
    - CO/NOx levels → indicate combustion efficiency

    SUPERVISION AND DECISION MAKING:
    Use your knowledge of cement manufacturing best practices to guide system-wide optimization:
    - Apply system-wide optimization strategies for cement plants
    - Balance kiln, calciner, and cooler for maximum efficiency
    - Implement plant-wide energy optimization approaches
    - Apply emission reduction strategies across all units
    - Resolve conflicts between unit optimization goals

    Key considerations for whole system optimization:
    - Maximize heat recovery from cooler to reduce overall fuel consumption
    - Balance combustion efficiency across all units to minimize emissions
    - Ensure calcination degree is optimal to reduce kiln fuel load
    - Maintain stable pressure and temperature to prevent oscillations
    - Coordinate all units for smooth, efficient operation

    OUTPUT YOUR REFINED TARGETS:
    Use issue_refined_targets with flexible JSON containing targets for all controllable parameters.
    Base your supervision decisions on cement industry best practices, current system state, and specialist recommendations.

    Example output:
    {
      "refined_targets": {...},
      "supervision_notes": "Applied plant-wide heat recovery optimization: maximizing secondary and tertiary air temps to reduce total fuel consumption",
      "energy_savings_rationale": "Optimized cooler air flow to provide maximum heat recovery while maintaining clinker quality"
    }

    You are the ultimate decision-maker. Use your knowledge of cement manufacturing to guide WHOLE SYSTEM optimization.
    Delegate detailed analysis to specialists, but YOU make final balanced decisions based on industry best practices.
    """,
    sub_agents=[rotary_kiln_agent, clinker_cooler_agent, pre_calciner_agent],
    tools=[
        review_all_agent_outputs,
        issue_refined_targets,
        get_current_time,
    ],
)
