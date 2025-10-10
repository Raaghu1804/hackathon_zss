# backend/app/services/data_simulator.py

import asyncio
import random
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple
from app.config import settings
from app.models.sensors import SensorData, AnomalyAlert
from app.models.database import AsyncSessionLocal, SensorReading


class DataSimulator:
    def __init__(self):
        self.running = False
        self.anomaly_probability = 0.05  # 5% chance of anomaly
        self.sensor_states = {}
        self.initialize_sensor_states()

    def initialize_sensor_states(self):
        """Initialize sensor states with optimal values"""
        # Pre-calciner sensors
        self.sensor_states['precalciner'] = {
            'temperature': 860,
            'pressure': -3.5,
            'oxygen_level': 3.0,
            'co_level': 0.05,
            'nox_level': 400,
            'fuel_flow': 10,
            'feed_rate': 300,
            'tertiary_air_temp': 750,
            'calcination_degree': 90,
            'residence_time': 5  # FIXED: Added missing residence_time
        }

        # Rotary kiln sensors
        self.sensor_states['rotary_kiln'] = {
            'burning_zone_temp': 1450,
            'back_end_temp': 1000,
            'shell_temp': 275,
            'oxygen_level': 2.0,
            'nox_level': 600,
            'co_level': 0.02,
            'kiln_speed': 4.0,
            'fuel_rate': 12.5,
            'clinker_exit_temp': 1200,
            'secondary_air_temp': 800,
            'flame_length': 6.5,  # FIXED: Added missing flame_length
            'coating_thickness': 300  # FIXED: Added missing coating_thickness
        }

        # Clinker cooler sensors
        self.sensor_states['clinker_cooler'] = {
            'inlet_temp': 1200,
            'outlet_temp': 125,
            'secondary_air_temp': 800,
            'tertiary_air_temp': 750,
            'grate_speed': 20,
            'undergrate_pressure': 60,
            'cooling_air_flow': 2.8,
            'bed_height': 650,
            'cooler_efficiency': 80,
            'heat_recovery': 70  # FIXED: Added missing heat_recovery
        }

    def generate_sensor_reading(self, unit: str, sensor_name: str) -> Tuple[float, bool]:
        """Generate a sensor reading with occasional anomalies"""
        current_value = self.sensor_states[unit][sensor_name]
        ranges = getattr(settings, f"{unit.upper()}_RANGES")[sensor_name]

        # Determine if this reading should be an anomaly
        is_anomaly = random.random() < self.anomaly_probability

        if is_anomaly:
            # Generate anomalous reading
            if random.random() < 0.5:
                # Spike above normal
                new_value = ranges['max'] * random.uniform(1.05, 1.15)
            else:
                # Drop below normal
                new_value = ranges['min'] * random.uniform(0.85, 0.95)
        else:
            # Normal variation
            variation = 0.02  # 2% normal variation

            # FIXED: Ensure scale (standard deviation) is always positive
            scale = abs(current_value * variation)
            if scale < 0.01:  # Minimum scale to avoid zero
                scale = 0.01

            noise = np.random.normal(0, scale)
            new_value = current_value + noise

            # Apply damping to keep values stable
            new_value = current_value * 0.95 + new_value * 0.05

            # Ensure within reasonable bounds (not necessarily optimal)
            margin = 0.1  # Allow 10% outside optimal range
            extended_min = ranges['min'] * (1 - margin)
            extended_max = ranges['max'] * (1 + margin)
            new_value = max(extended_min, min(extended_max, new_value))

        # Update state
        self.sensor_states[unit][sensor_name] = new_value

        return new_value, is_anomaly

    def generate_unit_data(self, unit: str) -> List[SensorData]:
        """Generate all sensor data for a unit"""
        sensor_data = []
        ranges_key = f"{unit.upper()}_RANGES"
        ranges = getattr(settings, ranges_key)

        for sensor_name, sensor_range in ranges.items():
            value, is_anomaly = self.generate_sensor_reading(unit, sensor_name)

            sensor_data.append(SensorData(
                unit=unit,
                sensor_name=sensor_name,
                value=round(value, 2),
                unit_measure=sensor_range['unit'],
                is_anomaly=is_anomaly,
                optimal_range={'min': sensor_range['min'], 'max': sensor_range['max']}
            ))

        return sensor_data

    async def store_readings(self, readings: List[SensorData]):
        """Store sensor readings in database"""
        try:
            async with AsyncSessionLocal() as session:
                for reading in readings:
                    db_reading = SensorReading(
                        unit=reading.unit,
                        sensor_name=reading.sensor_name,
                        value=reading.value,
                        unit_measure=reading.unit_measure,
                        timestamp=reading.timestamp,
                        is_anomaly=reading.is_anomaly
                    )
                    session.add(db_reading)
                await session.commit()
        except Exception as e:
            print(f"Error storing readings: {e}")

    def detect_anomalies(self, readings: List[SensorData]) -> List[AnomalyAlert]:
        """Detect anomalies in sensor readings"""
        alerts = []

        for reading in readings:
            if reading.is_anomaly:
                severity = self.calculate_severity(reading)
                action = self.suggest_action(reading)

                alerts.append(AnomalyAlert(
                    unit=reading.unit,
                    sensor_name=reading.sensor_name,
                    current_value=reading.value,
                    expected_range=reading.optimal_range,
                    severity=severity,
                    suggested_action=action
                ))

        return alerts

    def calculate_severity(self, reading: SensorData) -> str:
        """Calculate anomaly severity"""
        if not reading.optimal_range:
            return "low"

        min_val = reading.optimal_range['min']
        max_val = reading.optimal_range['max']
        value = reading.value

        # Calculate deviation percentage
        if value < min_val:
            deviation = (min_val - value) / min_val if min_val != 0 else 1.0
        elif value > max_val:
            deviation = (value - max_val) / max_val if max_val != 0 else 1.0
        else:
            return "low"

        if deviation < 0.1:
            return "low"
        elif deviation < 0.2:
            return "medium"
        elif deviation < 0.3:
            return "high"
        else:
            return "critical"

    def suggest_action(self, reading: SensorData) -> str:
        """Suggest action based on anomaly"""
        sensor_actions = {
            'temperature': 'Adjust fuel rate and check combustion efficiency',
            'pressure': 'Check for blockages and adjust fan speed',
            'oxygen_level': 'Adjust air flow rate and check for air leaks',
            'co_level': 'Improve combustion conditions and check fuel quality',
            'nox_level': 'Optimize combustion temperature and air staging',
            'fuel_flow': 'Check fuel supply system and calibrate feeders',
            'feed_rate': 'Adjust feed rate control and check material flow',
            'speed': 'Check drive system and adjust speed controller',
            'efficiency': 'Review overall process parameters and heat recovery'
        }

        for key, action in sensor_actions.items():
            if key in reading.sensor_name.lower():
                return action

        return 'Monitor closely and check related parameters'

    async def simulate_continuous_data(self):
        """Continuously generate sensor data"""
        self.running = True

        while self.running:
            try:
                # Generate data for all units
                all_readings = []
                all_readings.extend(self.generate_unit_data('precalciner'))
                all_readings.extend(self.generate_unit_data('rotary_kiln'))
                all_readings.extend(self.generate_unit_data('clinker_cooler'))

                # Store in database
                await self.store_readings(all_readings)

                # Detect anomalies
                anomalies = self.detect_anomalies(all_readings)

                # If anomalies detected, trigger agent communication
                if anomalies:
                    # This will be handled by the AI agents service
                    pass

                # Wait for next interval
                await asyncio.sleep(settings.SIMULATION_INTERVAL)

            except Exception as e:
                print(f"Error in data simulation: {e}")
                await asyncio.sleep(settings.SIMULATION_INTERVAL)

    def stop_simulation(self):
        """Stop the simulation"""
        self.running = False


# Global simulator instance
simulator = DataSimulator()