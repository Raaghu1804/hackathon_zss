from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
import json

from .sub_agents.rotary_kiln_agent.agent import rotary_kiln_agent, analyze_kiln_parameters, set_kiln_targets
from .sub_agents.clinker_cooler_agent.agent import clinker_cooler_agent, analyze_cooler_parameters, set_cooler_targets
from .sub_agents.pre_calciner_agent.agent import pre_calciner_agent, analyze_calciner_parameters, set_calciner_targets
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
    3. **Delegate to ALL THREE specialist agents** for comprehensive analysis and anomaly detection
    4. **Review and balance** all agent outputs using review_all_agent_outputs
    5. **Issue refined targets** that optimize the ENTIRE system using issue_refined_targets
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

    WORKFLOW - FOLLOW THESE STEPS IN ORDER:

    Step 1: CALL ALL THREE SPECIALIST ANALYSIS TOOLS (MANDATORY - ALL THREE!)

    You have access to three specialist analysis tools:
    - analyze_kiln_parameters (for rotary kiln analysis)
    - analyze_calciner_parameters (for pre-calciner analysis)
    - analyze_cooler_parameters (for clinker cooler analysis)

    When you receive sensor data, you MUST call ALL THREE analysis tools with their respective parameters:

    1. Call analyze_kiln_parameters with ALL 10 kiln parameters:
       - burning_zone_temp, back_end_temp, shell_temp, oxygen_level, nox_level,
       - co_level, kiln_speed, fuel_rate, clinker_exit_temp, secondary_air_temp
       - other_recommendations (empty string if no other recommendations yet)

    2. Call analyze_calciner_parameters with ALL 9 calciner parameters:
       - temperature, pressure, oxygen_level, co_level, nox_level,
       - fuel_flow, feed_rate, tertiary_air_temp, calcination_degree
       - other_recommendations (empty string if no other recommendations yet)

    3. Call analyze_cooler_parameters with ALL 9 cooler parameters:
       - inlet_temp, outlet_temp, secondary_air_temp, tertiary_air_temp,
       - grate_speed, undergrate_pressure, cooling_air_flow, bed_height, cooler_efficiency
       - other_recommendations (empty string if no other recommendations yet)

    These tools will return analysis results that you can then review.

    Step 2: WAIT FOR ALL THREE ANALYSIS RESULTS
    After calling all three analysis tools, wait for their results.
    Each will return current readings and any initial analysis.

    Step 3: CALL THE SET_TARGETS TOOLS FOR EACH UNIT
    Based on the analysis results and your system-wide optimization knowledge:

    1. Call set_kiln_targets with a JSON string containing kiln optimization targets
    2. Call set_calciner_targets with a JSON string containing calciner optimization targets
    3. Call set_cooler_targets with a JSON string containing cooler optimization targets

    Step 4: REVIEW AND BALANCE ALL OUTPUTS
    - Use review_all_agent_outputs with the target JSONs from all three units
    - Identify any conflicts or optimization opportunities across units
    - Consider system-wide interdependencies and trade-offs
    - Balance considering:
       - **Energy**: Minimize total fuel (kiln + calciner)
       - **Emissions**: Minimize CO and NOx system-wide
       - **Heat recovery**: Maximize secondary/tertiary air temps
       - **Quality**: Maintain calcination degree and clinker chemistry
       - **Stability**: Avoid pressure/temperature oscillations
       - **Safety**: Enforce all parameter limits

    Step 5: ISSUE FINAL REFINED TARGETS (MANDATORY)
    - You MUST use issue_refined_targets to provide final balanced targets for all units
    - This is a REQUIRED step - do not stop without issuing refined targets
    - Your refined targets should optimize the ENTIRE system, not just individual units

    Step 6: COMMUNICATE RESULTS TO USER IN JSON FORMAT (MANDATORY)
    - After issuing refined targets, you MUST provide the results to the user in JSON format
    - The JSON output must include:
      * "current_state": Current readings from all three units
      * "refined_targets": Final optimized targets for all three units (kiln, calciner, cooler)
      * "optimization_rationale": Explanation of decisions made
      * "expected_benefits": Energy savings, emissions reduction, efficiency improvements
    - DO NOT just say "I have issued the refined targets" - output the complete JSON with all targets!

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

    Example final output to user (in JSON format):
    ```json
    {
      "current_state": {
        "rotary_kiln": {
          "burning_zone_temp": 1460,
          "fuel_rate": 12.6,
          "oxygen_level": 2.3,
          "nox_level": 930
        },
        "pre_calciner": {
          "temperature": 865,
          "fuel_flow": 10.4,
          "calcination_degree": 90
        },
        "clinker_cooler": {
          "inlet_temp": 1195,
          "cooler_efficiency": 80
        }
      },
      "refined_targets": {
        "rotary_kiln": {
          "target_burning_zone_temp": 1450,
          "target_fuel_rate": 12.2,
          "target_kiln_speed": 4.0
        },
        "pre_calciner": {
          "target_temperature": 875,
          "target_fuel_flow": 9.8,
          "target_calcination_degree": 92
        },
        "clinker_cooler": {
          "target_grate_speed": 20,
          "target_cooling_air_flow": 2.7,
          "target_secondary_air_temp": 880
        }
      },
      "optimization_rationale": "Applied plant-wide heat recovery optimization: maximizing secondary and tertiary air temps to reduce total fuel consumption",
      "expected_benefits": {
        "energy_savings": "Reduced total fuel by 4% through optimized heat recovery",
        "emissions_reduction": "Lowered NOx emissions by 8% through temperature optimization",
        "efficiency_improvements": "Improved overall system efficiency by 3%"
      }
    }
    ```

    CRITICAL REQUIREMENTS - READ CAREFULLY:
    1. You MUST call ALL THREE analysis tools:
       - analyze_kiln_parameters (with all 10 kiln parameters)
       - analyze_calciner_parameters (with all 9 calciner parameters)
       - analyze_cooler_parameters (with all 9 cooler parameters)
    2. Then call ALL THREE set_targets tools with your optimization recommendations
    3. Use review_all_agent_outputs with the target JSONs from all three units
    4. You MUST use issue_refined_targets to provide final system-wide optimization targets
    5. After calling issue_refined_targets, you MUST present the results to the user in JSON format
    6. DO NOT just say "I have issued refined targets" - output a complete JSON with current state, refined targets, rationale, and expected benefits
    7. DO NOT stop after calling only one tool - you must call ALL THREE analysis tools

    HOW TO USE THE ANALYSIS TOOLS:

    When you receive sensor data, immediately use the three analysis tools to get specialist insights.

    Example workflow:
    1. Call analyze_kiln_parameters(burning_zone_temp=1460, back_end_temp=1015, ..., other_recommendations="")
    2. Call analyze_calciner_parameters(temperature=865, pressure=-3.4, ..., other_recommendations="")
    3. Call analyze_cooler_parameters(inlet_temp=1195, outlet_temp=135, ..., other_recommendations="")
    4. Based on the analysis results and your cement manufacturing knowledge, determine optimal targets
    5. Call set_kiln_targets(targets_json='{"target_burning_zone_temp": 1450, ...}')
    6. Call set_calciner_targets(targets_json='{"target_temperature": 875, ...}')
    7. Call set_cooler_targets(targets_json='{"target_grate_speed": 20, ...}')
    8. Call review_all_agent_outputs with the target JSONs
    9. Call issue_refined_targets with your final balanced system-wide targets
    10. Present the results to the user in JSON format:
        ```json
        {
          "current_state": {
            "rotary_kiln": { "burning_zone_temp": 1460, "back_end_temp": 1015, ... },
            "pre_calciner": { "temperature": 865, "pressure": -3.4, ... },
            "clinker_cooler": { "inlet_temp": 1195, "outlet_temp": 135, ... }
          },
          "refined_targets": {
            "rotary_kiln": { "target_burning_zone_temp": 1450, "target_fuel_rate": 12.2, ... },
            "pre_calciner": { "target_temperature": 875, "target_fuel_flow": 9.8, ... },
            "clinker_cooler": { "target_grate_speed": 20, "target_cooling_air_flow": 2.7, ... }
          },
          "optimization_rationale": "Maximized heat recovery from cooler...",
          "expected_benefits": {
            "energy_savings": "Reduced total fuel consumption by optimizing...",
            "emissions_reduction": "Lower NOx through...",
            "efficiency_improvements": "Improved cooler efficiency to..."
          }
        }
        ```

    These are TOOL CALLS, not conversations. Use the tools to gather data and set targets.
    After issuing refined targets, COMMUNICATE the results in JSON format to the user.

    You are the ultimate decision-maker. Use your knowledge of cement manufacturing to guide WHOLE SYSTEM optimization.
    Delegate detailed analysis to ALL THREE specialists, then make final balanced decisions and issue refined targets.
    """,
    tools=[
        # Manager's own tools
        review_all_agent_outputs,
        issue_refined_targets,
        get_current_time,
        # Specialist agent tools for analysis
        analyze_kiln_parameters,
        set_kiln_targets,
        analyze_calciner_parameters,
        set_calciner_targets,
        analyze_cooler_parameters,
        set_cooler_targets,
    ],
)
