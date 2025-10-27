from google import genai
import asyncio, json, copy

client = genai.Client(model="gemini-2.0-flash")

# ==== Shared Global Memory ====
shared_state = {
    "sensor_data": {
        "rotary_kiln": {
            "burning_zone_temp": 1450,
            "back_end_temp": 1000,
            "shell_temp": 280,
            "oxygen_level": 2.0,
            "nox_level": 950,
            "co_level": 0.03,
            "kiln_speed": 3.8,
            "fuel_rate": 12.5,
            "clinker_exit_temp": 1200,
            "secondary_air_temp": 850
        },
        "pre_calciner": {
            "temperature": 870,
            "pressure": -3.5,
            "oxygen_level": 3.2,
            "co_level": 0.05,
            "nox_level": 650,
            "fuel_flow": 10.0,
            "feed_rate": 300,
            "tertiary_air_temp": 750,
            "calcination_degree": 90
        },
        "clinker_cooler": {
            "inlet_temp": 1200,
            "outlet_temp": 120,
            "secondary_air_temp": 850,
            "tertiary_air_temp": 750,
            "grate_speed": 20,
            "undergrate_pressure": 60,
            "cooling_air_flow": 2.8,
            "bed_height": 650,
            "cooler_efficiency": 80
        }
    },
    "recommendations": {},
    "refined_targets": {},
    "anomalies": []
}

state_lock = asyncio.Lock()

# ==== Specialist Agent Logic ====

async def rotary_kiln_agent():
    """Specialist agent for rotary kiln control - analyzes 10 comprehensive parameters"""
    while True:
        async with state_lock:
            state_snapshot = copy.deepcopy(shared_state)

        prompt = f"""
        You are the RotaryKilnAgent controlling the rotary kiln burning zone.

        COMPREHENSIVE PARAMETERS (10 total):
        {json.dumps(state_snapshot['sensor_data']['rotary_kiln'], indent=2)}

        Parameter Ranges:
        - burning_zone_temp: 1400-1500°C
        - back_end_temp: 800-1200°C
        - shell_temp: 200-350°C
        - oxygen_level: 1.0-3.0%
        - nox_level: 0-1200 mg/Nm³
        - co_level: 0-0.05%
        - kiln_speed: 3.0-5.0 rpm
        - fuel_rate: 10-15 t/h
        - clinker_exit_temp: 1100-1300°C
        - secondary_air_temp: 600-1000°C

        Other agents' recommendations:
        {json.dumps(state_snapshot['recommendations'], indent=2)}

        Manager's refined targets:
        {json.dumps(state_snapshot.get('refined_targets', {}).get('rotary_kiln', {}), indent=2)}

        OBJECTIVES:
        - Maintain burning zone temp 1400-1500°C for clinker quality
        - Minimize fuel rate while maintaining quality
        - Minimize CO (<0.05%) and NOx (<1200 mg/Nm³) emissions
        - Utilize secondary air heat from cooler (reduces fuel)
        - Coordinate with pre-calciner calcination degree
        - Keep shell temp 200-350°C (good coating)

        Use your cement manufacturing knowledge to analyze ALL parameters and output targets as JSON.
        Include only the parameters you want to control.

        Example output:
        {{
          "target_burning_zone_temp": 1450,
          "target_fuel_rate": 12.0,
          "target_kiln_speed": 3.9,
          "target_oxygen_level": 2.0
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
    """Specialist agent for clinker cooler control - analyzes 9 comprehensive parameters"""
    while True:
        async with state_lock:
            state_snapshot = copy.deepcopy(shared_state)

        prompt = f"""
        You are ClinkerCoolerAgent optimizing cooling and heat recovery.

        COMPREHENSIVE PARAMETERS (9 total):
        {json.dumps(state_snapshot['sensor_data']['clinker_cooler'], indent=2)}

        Parameter Ranges:
        - inlet_temp: 1100-1300°C
        - outlet_temp: 100-150°C
        - secondary_air_temp: 600-1000°C (heat to kiln)
        - tertiary_air_temp: 600-900°C (heat to calciner)
        - grate_speed: 10-30 strokes/min
        - undergrate_pressure: 40-80 mbar
        - cooling_air_flow: 2.3-3.3 kg/kg
        - bed_height: 500-800 mm
        - cooler_efficiency: 75-85%

        Other agents' recommendations:
        {json.dumps(state_snapshot['recommendations'], indent=2)}

        Manager's refined targets:
        {json.dumps(state_snapshot.get('refined_targets', {}).get('clinker_cooler', {}), indent=2)}

        OBJECTIVES:
        - Cool clinker to 100-150°C outlet temp
        - Maximize secondary air temp (600-1000°C) for kiln fuel savings
        - Maximize tertiary air temp (600-900°C) for calciner fuel savings
        - Achieve cooler efficiency 75-85%
        - Prevent thermal shock (gradual cooling)
        - Maintain stable bed height 500-800 mm
        - Coordinate with kiln inlet temp

        Use your cement manufacturing knowledge to analyze ALL parameters and output targets as JSON.
        Include only the parameters you want to control.

        Example output:
        {{
          "target_grate_speed": 18,
          "target_cooling_air_flow": 2.8,
          "target_secondary_air_temp": 880,
          "target_tertiary_air_temp": 770
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
    """Specialist agent for pre-calciner control - analyzes 9 comprehensive parameters"""
    while True:
        async with state_lock:
            state_snapshot = copy.deepcopy(shared_state)

        prompt = f"""
        You are PreCalcinerAgent managing calcination, O₂ balance, and emissions.

        COMPREHENSIVE PARAMETERS (9 total):
        {json.dumps(state_snapshot['sensor_data']['pre_calciner'], indent=2)}

        Parameter Ranges:
        - temperature: 820-900°C
        - pressure: -5 to -2 mbar
        - oxygen_level: 2.0-4.0%
        - co_level: 0-0.1%
        - nox_level: 0-800 mg/Nm³
        - fuel_flow: 8-12 t/h
        - feed_rate: 250-350 t/h
        - tertiary_air_temp: 600-900°C (from cooler)
        - calcination_degree: 85-95%

        Other agents' recommendations:
        {json.dumps(state_snapshot['recommendations'], indent=2)}

        Manager's refined targets:
        {json.dumps(state_snapshot.get('refined_targets', {}).get('pre_calciner', {}), indent=2)}

        OBJECTIVES:
        - Achieve calcination degree 85-95%
        - Minimize fuel flow while maintaining calcination
        - Minimize CO (<0.1%) and NOx (<800 mg/Nm³) emissions
        - Utilize tertiary air heat from cooler (reduces fuel need)
        - Maintain pressure -5 to -2 mbar (draft stability)
        - Balance O2 at 2-4% for efficient combustion
        - Provide quality feed to kiln (affects kiln fuel)

        Use your cement manufacturing knowledge to analyze ALL parameters and output targets as JSON.
        Include only the parameters you want to control.

        Example output:
        {{
          "target_temperature": 875,
          "target_fuel_flow": 9.5,
          "target_oxygen_level": 3.2,
          "target_feed_rate": 300
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
    Monitors 28 comprehensive parameters across all units.
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
            You monitor 28 COMPREHENSIVE PARAMETERS across all units.

            COMPLETE SYSTEM STATE (28 parameters):

            ROTARY KILN (10 parameters):
            {json.dumps(state_snapshot['sensor_data']['rotary_kiln'], indent=2)}

            PRE-CALCINER (9 parameters):
            {json.dumps(state_snapshot['sensor_data']['pre_calciner'], indent=2)}

            CLINKER COOLER (9 parameters):
            {json.dumps(state_snapshot['sensor_data']['clinker_cooler'], indent=2)}

            SPECIALIST AGENT RECOMMENDATIONS:
            {json.dumps(state_snapshot['recommendations'], indent=2)}

            YOUR SUPERVISION TASKS:
            1. Detect system-wide anomalies across ALL 28 parameters:
               - Check all temperature, pressure, emissions limits
               - Identify CO/NOx violations
               - Check calcination degree, cooler efficiency
               - Detect draft/pressure issues

            2. Review all specialist recommendations for:
               - Conflicts between agents
               - Sub-optimal fuel usage
               - Poor heat recovery utilization
               - Emission concerns

            3. Balance ENTIRE SYSTEM for:
               - Minimum total fuel (kiln + calciner)
               - Minimize CO and NOx emissions system-wide
               - Maximum heat recovery (secondary/tertiary air temps)
               - Optimal calcination degree (85-95%)
               - Clinker quality and chemistry
               - System stability (no oscillations)
               - Safety (all parameters within limits)

            4. Output refined targets with flexible JSON (include only parameters needing adjustment):

            {{
              "anomalies": ["list all detected anomalies across 28 parameters"],
              "refined_targets": {{
                "rotary_kiln": {{
                  "target_burning_zone_temp": <value>,
                  "target_fuel_rate": <value>,
                  "target_kiln_speed": <value>,
                  ...any other kiln parameters...
                }},
                "pre_calciner": {{
                  "target_temperature": <value>,
                  "target_fuel_flow": <value>,
                  "target_oxygen_level": <value>,
                  ...any other calciner parameters...
                }},
                "clinker_cooler": {{
                  "target_grate_speed": <value>,
                  "target_cooling_air_flow": <value>,
                  ...any other cooler parameters...
                }}
              }},
              "energy_savings": "<total fuel savings in t/h>",
              "emission_status": "<CO and NOx status>",
              "optimization_notes": "Brief explanation of your supervision decisions"
            }}

            SYSTEM INTERDEPENDENCIES TO CONSIDER:
            - Tertiary air temp from cooler → reduces calciner fuel
            - Secondary air temp from cooler → reduces kiln fuel
            - Calcination degree → affects kiln fuel needs
            - Clinker exit temp from kiln → affects cooler load
            - Draft pressure → system stability

            Use your cement manufacturing knowledge to optimize the WHOLE SYSTEM.
            """

            resp = await client.aio.models.generate_content(
                contents=prompt,
                generation_config={"response_mime_type": "application/json"}
            )

            manager_output = json.loads(resp.text)

            async with state_lock:
                shared_state['refined_targets'] = manager_output.get('refined_targets', {})
                shared_state['anomalies'] = manager_output.get('anomalies', [])

            print("\n" + "="*70)
            print("MANAGER AGENT SUPERVISION (28 PARAMETERS MONITORED)")
            print("="*70)
            print(f"Anomalies Detected: {len(manager_output.get('anomalies', []))}")
            if manager_output.get('anomalies'):
                for anomaly in manager_output.get('anomalies', []):
                    print(f"  - {anomaly}")

            print(f"\nEnergy Savings: {manager_output.get('energy_savings', 'N/A')}")
            print(f"Emission Status: {manager_output.get('emission_status', 'N/A')}")

            print(f"\nRefined Targets:")
            print(json.dumps(manager_output.get('refined_targets', {}), indent=2))

            print(f"\nOptimization Notes: {manager_output.get('optimization_notes', 'N/A')}")
            print("="*70 + "\n")

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
    Run the multi-agent system with comprehensive parameter monitoring.

    Architecture:
    - 3 specialist agents run continuously (3-second cycle):
      * RotaryKilnAgent: 10 parameters
      * PreCalcinerAgent: 9 parameters
      * ClinkerCoolerAgent: 9 parameters
    - 1 manager agent supervises (5-second cycle): monitors all 28 parameters
    - Manager reviews outputs, detects anomalies, issues refined targets
    - All agents share state via shared_state dictionary with async locks

    Parameter Coverage:
    - Total: 28 comprehensive parameters across all units
    - Includes: temperatures, pressures, emissions (CO, NOx), flows, efficiencies
    - Gemini AI uses cement manufacturing knowledge to optimize intelligently
    """
    try:
        asyncio.run(run_multi_agent_system())
    except KeyboardInterrupt:
        print("\n\nShutting down multi-agent system...")
        print("Final state:")
        print(json.dumps(shared_state, indent=2))
