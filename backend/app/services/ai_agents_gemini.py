from google import genai
import asyncio, json, copy

client = genai.Client(model="gemini-2.0-flash")

# ==== Shared Global Memory ====
shared_state = {
    "sensor_data": {
        "rotary_kiln": {"kiln_temp": 1420, "feed_rate": 12500, "fuel_rate": 820},
        "clinker_cooler": {"clinker_temp": 300, "air_pressure": 160, "grate_speed": 2.0},
        "pre_calciner": {"calciner_temp": 850, "o2_concentration": 5.1, "fuel_flow": 470}
    },
    "recommendations": {},
    "refined_targets": {},
    "anomalies": []
}

state_lock = asyncio.Lock()

# ==== Specialist Agent Logic ====

async def rotary_kiln_agent():
    """Specialist agent for rotary kiln control"""
    while True:
        async with state_lock:
            state_snapshot = copy.deepcopy(shared_state)

        prompt = f"""
        You are the RotaryKilnAgent controlling the burning zone.
        Optimise for clinker quality and energy efficiency.

        Current Sensor data:
        {json.dumps(state_snapshot['sensor_data']['rotary_kiln'], indent=2)}

        Other agents' latest recommendations:
        {json.dumps(state_snapshot['recommendations'], indent=2)}

        Manager's refined targets (if any):
        {json.dumps(state_snapshot.get('refined_targets', {}).get('rotary_kiln', {}), indent=2)}

        Consider:
        - Pre-calciner feed quality affects your input
        - Your output temperature affects cooler operations
        - Maintain kiln temp 1400-1500°C for optimal clinker formation

        Output only numeric targets as JSON:
        {{
          "target_kiln_temp": <value>,
          "target_fuel_rate": <value>,
          "target_rotation_speed": <value>
        }}
        """
        resp = await client.aio.models.generate_content(
            contents=prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        async with state_lock:
            shared_state['recommendations']['rotary_kiln'] = json.loads(resp.text)
        print("RotaryKilnAgent →", shared_state['recommendations']['rotary_kiln'])
        await asyncio.sleep(3)


async def clinker_cooler_agent():
    """Specialist agent for clinker cooler control"""
    while True:
        async with state_lock:
            state_snapshot = copy.deepcopy(shared_state)

        prompt = f"""
        You are ClinkerCoolerAgent optimising cooling and heat recovery.

        Current Sensor data:
        {json.dumps(state_snapshot['sensor_data']['clinker_cooler'], indent=2)}

        Other agents' latest recommendations:
        {json.dumps(state_snapshot['recommendations'], indent=2)}

        Manager's refined targets (if any):
        {json.dumps(state_snapshot.get('refined_targets', {}).get('clinker_cooler', {}), indent=2)}

        Consider:
        - Kiln output temperature affects your cooling load
        - Recovered heat should be sent to pre-calciner
        - Target clinker exit temp < 100°C

        Output numeric targets as JSON:
        {{
          "target_air_pressure": <value>,
          "target_grate_speed": <value>
        }}
        """
        resp = await client.aio.models.generate_content(
            contents=prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        async with state_lock:
            shared_state['recommendations']['clinker_cooler'] = json.loads(resp.text)
        print("ClinkerCoolerAgent →", shared_state['recommendations']['clinker_cooler'])
        await asyncio.sleep(3)


async def pre_calciner_agent():
    """Specialist agent for pre-calciner control"""
    while True:
        async with state_lock:
            state_snapshot = copy.deepcopy(shared_state)

        prompt = f"""
        You are PreCalcinerAgent managing calcination and O₂ balance.

        Current Sensor data:
        {json.dumps(state_snapshot['sensor_data']['pre_calciner'], indent=2)}

        Other agents' latest recommendations:
        {json.dumps(state_snapshot['recommendations'], indent=2)}

        Manager's refined targets (if any):
        {json.dumps(state_snapshot.get('refined_targets', {}).get('pre_calciner', {}), indent=2)}

        Consider:
        - Your calcination quality affects kiln performance
        - O2 levels (3-6%) impact overall fuel efficiency
        - Temperature 850-950°C optimal for calcination

        Output numeric targets as JSON:
        {{
          "target_calciner_temp": <value>,
          "target_o2_concentration": <value>,
          "target_fuel_flow": <value>
        }}
        """
        resp = await client.aio.models.generate_content(
            contents=prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        async with state_lock:
            shared_state['recommendations']['pre_calciner'] = json.loads(resp.text)
        print("PreCalcinerAgent →", shared_state['recommendations']['pre_calciner'])
        await asyncio.sleep(3)


# ==== Manager Agent (Supervisor) ====

async def manager_agent():
    """
    Manager agent that supervises all specialist agents.
    Reviews their outputs, detects anomalies, and issues refined balanced targets.
    """
    # Wait a bit for specialist agents to initialize
    await asyncio.sleep(5)

    while True:
        async with state_lock:
            state_snapshot = copy.deepcopy(shared_state)

        # Only run if we have recommendations from all agents
        if (len(state_snapshot['recommendations']) >= 3 and
            'rotary_kiln' in state_snapshot['recommendations'] and
            'pre_calciner' in state_snapshot['recommendations'] and
            'clinker_cooler' in state_snapshot['recommendations']):

            prompt = f"""
            You are the ManagerAgent - supervisor of the cement clinkerization process.

            CURRENT SYSTEM STATE:

            Sensor Data:
            {json.dumps(state_snapshot['sensor_data'], indent=2)}

            Specialist Agent Recommendations:
            {json.dumps(state_snapshot['recommendations'], indent=2)}

            YOUR TASKS:
            1. Detect any system-wide anomalies (temperature limits, O2 levels, etc.)
            2. Review all agent recommendations for conflicts or inefficiencies
            3. Balance the entire system for:
               - Minimum total fuel consumption (kiln + calciner)
               - Optimal clinker quality
               - Maximum heat recovery from cooler to calciner
               - Safety (temp < 1550°C in kiln, O2 2-7% in calciner)

            4. Output refined targets that optimize the WHOLE SYSTEM:

            {{
              "anomalies": ["list any detected anomalies or empty array"],
              "refined_targets": {{
                "rotary_kiln": {{
                  "target_kiln_temp": <value>,
                  "target_fuel_rate": <value>,
                  "target_rotation_speed": <value>
                }},
                "pre_calciner": {{
                  "target_calciner_temp": <value>,
                  "target_o2_concentration": <value>,
                  "target_fuel_flow": <value>
                }},
                "clinker_cooler": {{
                  "target_air_pressure": <value>,
                  "target_grate_speed": <value>
                }}
              }},
              "optimization_notes": "Brief explanation of your supervision decisions"
            }}
            """

            resp = await client.aio.models.generate_content(
                contents=prompt,
                generation_config={"response_mime_type": "application/json"}
            )

            manager_output = json.loads(resp.text)

            async with state_lock:
                shared_state['refined_targets'] = manager_output.get('refined_targets', {})
                shared_state['anomalies'] = manager_output.get('anomalies', [])

            print("\n" + "="*60)
            print("MANAGER AGENT SUPERVISION:")
            print("="*60)
            print(f"Anomalies: {manager_output.get('anomalies', [])}")
            print(f"\nRefined Targets:")
            print(json.dumps(manager_output.get('refined_targets', {}), indent=2))
            print(f"\nNotes: {manager_output.get('optimization_notes', 'N/A')}")
            print("="*60 + "\n")

        await asyncio.sleep(5)  # Manager runs less frequently than specialist agents


# ==== Main Runner ====

async def run_multi_agent_system():
    """
    Main function to run all agents (3 specialists + 1 manager supervisor).
    """
    print("\n" + "="*60)
    print("CEMENT MULTI-AGENT SYSTEM WITH MANAGER SUPERVISION")
    print("="*60)
    print("Starting 4 agents:")
    print("  - RotaryKilnAgent (specialist)")
    print("  - PreCalcinerAgent (specialist)")
    print("  - ClinkerCoolerAgent (specialist)")
    print("  - ManagerAgent (supervisor)")
    print("="*60 + "\n")

    # Run all agents concurrently
    await asyncio.gather(
        rotary_kiln_agent(),
        pre_calciner_agent(),
        clinker_cooler_agent(),
        manager_agent(),
    )


# ==== Entry Point ====

if __name__ == "__main__":
    """
    Run the multi-agent system.

    Architecture:
    - 3 specialist agents run continuously (3-second cycle)
    - 1 manager agent supervises (5-second cycle)
    - Manager reviews all outputs, detects anomalies, issues refined targets
    - All agents share state via shared_state dictionary with async locks
    """
    try:
        asyncio.run(run_multi_agent_system())
    except KeyboardInterrupt:
        print("\n\nShutting down multi-agent system...")
        print("Final state:")
        print(json.dumps(shared_state, indent=2))
