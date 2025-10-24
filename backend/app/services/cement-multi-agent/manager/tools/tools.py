from datetime import datetime
from google.adk.tools.tool_context import ToolContext
import json


def get_current_time() -> dict:
    """
    Get the current time in the format YYYY-MM-DD HH:MM:SS
    """
    return {
        "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def get_sensor_data(
    unit: str,
    tool_context: ToolContext,
) -> dict:
    """
    Retrieve sensor data for a specific unit (rotary_kiln, pre_calciner, or clinker_cooler).
    """
    print(f"--- Tool: get_sensor_data called for {unit} ---")

    # Get shared sensor data from state
    shared_state = tool_context.state.get("shared_sensor_data", {})
    sensor_data = shared_state.get(unit, {})

    return {
        "status": "success",
        "unit": unit,
        "sensor_data": sensor_data,
    }


def update_sensor_data(
    unit: str,
    sensor_readings: str,
    tool_context: ToolContext,
) -> dict:
    """
    Update sensor data for a specific unit.
    """
    print(f"--- Tool: update_sensor_data called for {unit} ---")

    try:
        readings = json.loads(sensor_readings)
    except:
        return {
            "status": "error",
            "message": "Failed to parse sensor readings",
        }

    # Initialize shared state if not exists
    if "shared_sensor_data" not in tool_context.state:
        tool_context.state["shared_sensor_data"] = {}

    # Update sensor data for the unit
    tool_context.state["shared_sensor_data"][unit] = readings

    return {
        "status": "success",
        "unit": unit,
        "updated_data": readings,
    }


def get_all_recommendations(
    tool_context: ToolContext,
) -> dict:
    """
    Retrieve recommendations from all agents.
    """
    print("--- Tool: get_all_recommendations called ---")

    recommendations = tool_context.state.get("agent_recommendations", {})

    return {
        "status": "success",
        "recommendations": recommendations,
    }


def update_recommendations(
    agent_name: str,
    recommendations: str,
    tool_context: ToolContext,
) -> dict:
    """
    Update recommendations from a specific agent.
    """
    print(f"--- Tool: update_recommendations called for {agent_name} ---")

    try:
        recs = json.loads(recommendations)
    except:
        return {
            "status": "error",
            "message": "Failed to parse recommendations",
        }

    # Initialize recommendations state if not exists
    if "agent_recommendations" not in tool_context.state:
        tool_context.state["agent_recommendations"] = {}

    # Update recommendations for the agent
    tool_context.state["agent_recommendations"][agent_name] = recs

    return {
        "status": "success",
        "agent": agent_name,
        "updated_recommendations": recs,
    }
