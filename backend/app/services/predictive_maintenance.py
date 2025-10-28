# backend/app/services/predictive_maintenance.py

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any
from sqlalchemy import select
from app.models.database import AsyncSessionLocal, SensorReading
from app.services.gemini_service import gemini_service
import json


class PredictiveMaintenanceEngine:
    """Advanced predictive maintenance using time series forecasting"""

    def __init__(self):
        self.prediction_horizon = 72  # hours
        self.maintenance_thresholds = {
            'precalciner': {
                'refractory_wear': 0.75,
                'burner_efficiency': 0.80,
                'coating_stability': 0.70
            },
            'rotary_kiln': {
                'refractory_life': 0.80,
                'bearing_condition': 0.85,
                'shell_integrity': 0.75
            },
            'clinker_cooler': {
                'grate_wear': 0.70,
                'fan_bearing': 0.85,
                'plate_integrity': 0.80
            }
        }

    async def forecast_anomalies(self, unit: str, hours_ahead: int = 24) -> Dict[str, Any]:
        """Forecast potential anomalies using historical patterns"""

        async with AsyncSessionLocal() as session:
            # Get last 7 days of data
            cutoff_time = datetime.utcnow() - timedelta(days=7)
            result = await session.execute(
                select(SensorReading).where(
                    SensorReading.unit == unit,
                    SensorReading.timestamp >= cutoff_time
                ).order_by(SensorReading.timestamp)
            )
            readings = result.scalars().all()

        if len(readings) < 100:
            return {"error": "Insufficient historical data"}

        # Prepare time series data
        sensor_data = {}
        for reading in readings:
            if reading.sensor_name not in sensor_data:
                sensor_data[reading.sensor_name] = []
            sensor_data[reading.sensor_name].append({
                'timestamp': reading.timestamp.isoformat(),
                'value': reading.value,
                'is_anomaly': reading.is_anomaly
            })

        # Use Gemini for intelligent forecasting
        forecast = await self._gemini_forecast(unit, sensor_data, hours_ahead)

        # Calculate maintenance scores
        maintenance_scores = await self._calculate_maintenance_scores(unit, sensor_data)

        # Identify critical maintenance windows
        maintenance_windows = self._identify_maintenance_windows(forecast, maintenance_scores)

        return {
            'unit': unit,
            'forecast_horizon_hours': hours_ahead,
            'predicted_anomalies': forecast.get('predicted_anomalies', []),
            'maintenance_scores': maintenance_scores,
            'recommended_maintenance': maintenance_windows,
            'estimated_downtime_hours': self._estimate_downtime(maintenance_windows),
            'cost_impact': self._estimate_cost_impact(maintenance_windows),
            'confidence_score': forecast.get('confidence', 0.0)
        }

    async def _gemini_forecast(self, unit: str, sensor_data: Dict, hours_ahead: int) -> Dict[str, Any]:
        """Use Gemini for intelligent anomaly forecasting"""

        # Prepare data summary for Gemini
        data_summary = {}
        for sensor, values in sensor_data.items():
            recent_values = values[-100:]  # Last 100 readings
            data_summary[sensor] = {
                'current_value': recent_values[-1]['value'],
                'trend': 'increasing' if recent_values[-1]['value'] > recent_values[0]['value'] else 'decreasing',
                'volatility': np.std([v['value'] for v in recent_values]),
                'anomaly_rate': sum(1 for v in recent_values if v.get('is_anomaly', False)) / len(recent_values)
            }

        prompt = f"""
        As a predictive maintenance expert for cement plants, analyze this {unit} data and forecast potential issues:

        Current Sensor Status:
        {json.dumps(data_summary, indent=2)}

        Forecast Period: {hours_ahead} hours

        Provide predictions in JSON format:
        {{
            "predicted_anomalies": [
                {{
                    "sensor_name": "sensor name",
                    "estimated_time_hours": hours until anomaly,
                    "severity": "low/medium/high/critical",
                    "probability": 0-1,
                    "root_cause": "explanation",
                    "preventive_action": "specific action"
                }}
            ],
            "confidence": 0-1,
            "key_indicators": ["list of concerning trends"]
        }}
        """

        try:
            response = await gemini_service.model.generate_content(prompt)
            result_text = response.text.strip()
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]
            return json.loads(result_text.strip())
        except Exception as e:
            print(f"Gemini forecast error: {e}")
            return {'predicted_anomalies': [], 'confidence': 0.0, 'key_indicators': []}

    async def _calculate_maintenance_scores(self, unit: str, sensor_data: Dict) -> Dict[str, float]:
        """Calculate health scores for different components"""

        scores = {}

        # Calculate component-specific scores based on sensor patterns
        if unit == 'precalciner':
            scores['refractory_wear'] = self._assess_refractory_condition(sensor_data)
            scores['burner_efficiency'] = self._assess_burner_efficiency(sensor_data)
            scores['coating_stability'] = self._assess_coating_stability(sensor_data)

        elif unit == 'rotary_kiln':
            scores['refractory_life'] = self._assess_refractory_condition(sensor_data)
            scores['bearing_condition'] = self._assess_bearing_condition(sensor_data)
            scores['shell_integrity'] = self._assess_shell_integrity(sensor_data)

        elif unit == 'clinker_cooler':
            scores['grate_wear'] = self._assess_grate_wear(sensor_data)
            scores['fan_bearing'] = self._assess_bearing_condition(sensor_data)
            scores['plate_integrity'] = self._assess_plate_integrity(sensor_data)

        return scores

    def _assess_refractory_condition(self, sensor_data: Dict) -> float:
        """Assess refractory lining condition from temperature patterns"""
        temp_sensors = [k for k in sensor_data.keys() if 'temp' in k.lower()]
        if not temp_sensors:
            return 1.0

        # High shell temps indicate refractory wear
        shell_temps = sensor_data.get('shell_temp', [])
        if shell_temps:
            recent = [v['value'] for v in shell_temps[-50:]]
            avg_temp = np.mean(recent)
            # Normalize: 350°C is critical, 200°C is good
            score = max(0, 1 - (avg_temp - 200) / 150)
            return score
        return 0.9

    def _assess_burner_efficiency(self, sensor_data: Dict) -> float:
        """Assess burner efficiency from fuel and temperature data"""
        fuel_flow = sensor_data.get('fuel_flow', [])
        temp = sensor_data.get('temperature', [])

        if fuel_flow and temp:
            recent_fuel = [v['value'] for v in fuel_flow[-50:]]
            recent_temp = [v['value'] for v in temp[-50:]]

            # Efficiency decreases if fuel increases but temp doesn't
            fuel_trend = np.polyfit(range(len(recent_fuel)), recent_fuel, 1)[0]
            temp_trend = np.polyfit(range(len(recent_temp)), recent_temp, 1)[0]

            if fuel_trend > 0 and temp_trend < 0:
                return 0.6  # Poor efficiency
            return 0.9
        return 0.85

    def _assess_coating_stability(self, sensor_data: Dict) -> float:
        """Assess coating stability from temperature variations"""
        temp = sensor_data.get('temperature', [])
        if temp:
            recent = [v['value'] for v in temp[-50:]]
            volatility = np.std(recent)
            # Higher volatility indicates coating issues
            score = max(0, 1 - volatility / 50)
            return score
        return 0.85

    def _assess_bearing_condition(self, sensor_data: Dict) -> float:
        """Assess bearing condition from speed and vibration patterns"""
        speed_sensors = [k for k in sensor_data.keys() if 'speed' in k.lower()]
        if speed_sensors:
            speed_data = sensor_data[speed_sensors[0]]
            recent = [v['value'] for v in speed_data[-50:]]
            # Look for irregular patterns
            variations = np.diff(recent)
            irregularity = np.std(variations)
            score = max(0, 1 - irregularity / 2)
            return score
        return 0.9

    def _assess_shell_integrity(self, sensor_data: Dict) -> float:
        """Assess kiln shell integrity"""
        shell_temp = sensor_data.get('shell_temp', [])
        if shell_temp:
            recent = [v['value'] for v in shell_temp[-50:]]
            # Look for hot spots (high variability)
            variability = np.std(recent)
            score = max(0, 1 - variability / 100)
            return score
        return 0.85

    def _assess_grate_wear(self, sensor_data: Dict) -> float:
        """Assess cooler grate wear"""
        grate_speed = sensor_data.get('grate_speed', [])
        if grate_speed:
            recent = [v['value'] for v in grate_speed[-50:]]
            avg_speed = np.mean(recent)
            # Lower speeds may indicate wear
            score = min(1.0, avg_speed / 20)
            return score
        return 0.85

    def _assess_plate_integrity(self, sensor_data: Dict) -> float:
        """Assess cooler plate integrity"""
        efficiency = sensor_data.get('cooler_efficiency', [])
        if efficiency:
            recent = [v['value'] for v in efficiency[-50:]]
            avg_eff = np.mean(recent)
            score = avg_eff / 85  # 85% is target efficiency
            return min(1.0, score)
        return 0.8

    def _identify_maintenance_windows(self, forecast: Dict, scores: Dict) -> List[Dict]:
        """Identify optimal maintenance windows"""
        windows = []

        # Check critical scores
        for component, score in scores.items():
            threshold = self.maintenance_thresholds.get(component, 0.75)
            if score < threshold:
                urgency = 'critical' if score < 0.6 else 'high' if score < 0.7 else 'medium'
                windows.append({
                    'component': component,
                    'current_score': score,
                    'urgency': urgency,
                    'recommended_window_days': 7 if urgency == 'critical' else 14 if urgency == 'high' else 30,
                    'estimated_duration_hours': self._estimate_maintenance_duration(component)
                })

        # Add predictive anomalies
        for anomaly in forecast.get('predicted_anomalies', []):
            if anomaly.get('severity') in ['high', 'critical']:
                windows.append({
                    'component': anomaly['sensor_name'],
                    'current_score': 1 - anomaly.get('probability', 0),
                    'urgency': anomaly['severity'],
                    'recommended_window_days': max(1, int(anomaly.get('estimated_time_hours', 24) / 24)),
                    'estimated_duration_hours': 8,
                    'preventive_action': anomaly.get('preventive_action', '')
                })

        return sorted(windows, key=lambda x: x['current_score'])

    def _estimate_maintenance_duration(self, component: str) -> int:
        """Estimate maintenance duration in hours"""
        durations = {
            'refractory_wear': 120,
            'refractory_life': 120,
            'burner_efficiency': 8,
            'bearing_condition': 16,
            'grate_wear': 24,
            'shell_integrity': 48,
            'coating_stability': 12
        }
        return durations.get(component, 12)

    def _estimate_downtime(self, windows: List[Dict]) -> float:
        """Estimate total downtime needed"""
        return sum(w['estimated_duration_hours'] for w in windows)

    def _estimate_cost_impact(self, windows: List[Dict]) -> Dict[str, float]:
        """Estimate cost impact of maintenance"""
        maintenance_cost = sum(w['estimated_duration_hours'] * 5000 for w in windows)  # $5k/hour
        production_loss = sum(w['estimated_duration_hours'] * 285 * 50 for w in windows)  # 285 t/h @ $50/t

        return {
            'maintenance_cost_usd': maintenance_cost,
            'production_loss_usd': production_loss,
            'total_cost_usd': maintenance_cost + production_loss,
            'cost_if_failure_usd': (maintenance_cost + production_loss) * 3  # 3x cost if reactive
        }


# Global instance
predictive_maintenance = PredictiveMaintenanceEngine()