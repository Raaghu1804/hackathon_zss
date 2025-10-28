# backend/app/services/carbon_footprint_tracker.py

from typing import Dict, List, Any
from datetime import datetime, timedelta
from sqlalchemy import select, func
from app.models.database import AsyncSessionLocal, SensorReading, ProcessOptimization
import numpy as np


class CarbonFootprintTracker:
    """Track and optimize carbon emissions with sustainability scoring"""

    def __init__(self):
        # Emission factors (kg CO2 per unit)
        self.emission_factors = {
            'electricity': 0.82,  # kg CO2/kWh (India grid average)
            'coal': 94.6,  # kg CO2/GJ
            'diesel': 2.68,  # kg CO2/liter
            'clinker_calcination': 525,  # kg CO2/tonne clinker (process emissions)
            'transport': 0.12  # kg CO2/tonne-km
        }

        # Industry benchmarks (kg CO2/tonne cement)
        self.benchmarks = {
            'world_average': 650,
            'india_average': 720,
            'best_in_class': 550,
            'european_standard': 600,
            'target_2030': 520
        }

        # Sustainability weights for scoring
        self.sustainability_weights = {
            'carbon_intensity': 0.35,
            'alternative_fuel_rate': 0.25,
            'energy_efficiency': 0.20,
            'waste_heat_recovery': 0.10,
            'circular_economy': 0.10
        }

    async def calculate_real_time_footprint(self, unit: str = None) -> Dict[str, Any]:
        """Calculate real-time carbon footprint"""

        async with AsyncSessionLocal() as session:
            # Get last hour of data
            cutoff_time = datetime.utcnow() - timedelta(hours=1)

            query = select(SensorReading).where(SensorReading.timestamp >= cutoff_time)
            if unit:
                query = query.where(SensorReading.unit == unit)

            result = await session.execute(query.order_by(SensorReading.timestamp.desc()))
            readings = result.scalars().all()

        if not readings:
            return {'error': 'No recent data available'}

        # Calculate emissions by source
        emissions = self._calculate_emissions_breakdown(readings)

        # Calculate production rate
        production_rate = self._estimate_production_rate(readings)

        # Calculate carbon intensity
        carbon_intensity = emissions['total_kg_co2_per_hour'] / production_rate if production_rate > 0 else 0

        # Generate insights
        insights = self._generate_insights(carbon_intensity, emissions)

        return {
            'timestamp': datetime.utcnow().isoformat(),
            'unit': unit or 'all',
            'emissions_breakdown': emissions,
            'production_rate_tonnes_per_hour': round(production_rate, 2),
            'carbon_intensity_kg_co2_per_tonne': round(carbon_intensity, 2),
            'benchmark_comparison': self._compare_to_benchmarks(carbon_intensity),
            'insights': insights,
            'sustainability_score': self._calculate_sustainability_score(emissions, carbon_intensity)
        }

    def _calculate_emissions_breakdown(self, readings: List) -> Dict[str, Any]:
        """Break down emissions by source"""

        emissions = {
            'fuel_combustion': 0,
            'electricity': 0,
            'process_emissions': 0,
            'total_kg_co2_per_hour': 0
        }

        # Group readings by sensor
        sensor_data = {}
        for reading in readings:
            if reading.sensor_name not in sensor_data:
                sensor_data[reading.sensor_name] = []
            sensor_data[reading.sensor_name].append(reading.value)

        # Calculate fuel combustion emissions
        fuel_sensors = ['fuel_flow', 'fuel_rate']
        for sensor in fuel_sensors:
            if sensor in sensor_data:
                avg_fuel_rate = np.mean(sensor_data[sensor])  # tonnes/hour
                # Convert to GJ: 1 tonne coal ≈ 25.5 GJ
                fuel_gj = avg_fuel_rate * 25.5
                emissions['fuel_combustion'] += fuel_gj * self.emission_factors['coal']

        # Calculate electricity emissions
        # Estimate from motor loads (simplified)
        power_estimate = 30000  # kW (typical for cement plant)
        emissions['electricity'] = power_estimate * self.emission_factors['electricity']

        # Calculate process emissions (clinker calcination)
        # Estimate production rate
        production_rate = self._estimate_production_rate(readings)
        # Process emissions from CaCO3 decomposition
        emissions['process_emissions'] = production_rate * self.emission_factors['clinker_calcination']

        emissions['total_kg_co2_per_hour'] = sum([
            emissions['fuel_combustion'],
            emissions['electricity'],
            emissions['process_emissions']
        ])

        # Convert to percentages
        total = emissions['total_kg_co2_per_hour']
        emissions['breakdown_percent'] = {
            'fuel_combustion': round(emissions['fuel_combustion'] / total * 100, 1) if total > 0 else 0,
            'electricity': round(emissions['electricity'] / total * 100, 1) if total > 0 else 0,
            'process_emissions': round(emissions['process_emissions'] / total * 100, 1) if total > 0 else 0
        }

        return emissions

    def _estimate_production_rate(self, readings: List) -> float:
        """Estimate current production rate in tonnes/hour"""

        # Look for production-related sensors
        sensor_data = {}
        for reading in readings:
            if reading.sensor_name not in sensor_data:
                sensor_data[reading.sensor_name] = []
            sensor_data[reading.sensor_name].append(reading.value)

        # Base rate on feed rate and efficiency
        if 'feed_rate' in sensor_data:
            avg_feed_rate = np.mean(sensor_data['feed_rate'])
            # Assuming ~90% conversion efficiency
            return avg_feed_rate * 0.9

        # Fallback to typical production rate
        return 285  # tonnes/hour (from README)

    def _compare_to_benchmarks(self, carbon_intensity: float) -> Dict[str, Any]:
        """Compare current performance to industry benchmarks"""

        comparisons = {}
        for benchmark_name, benchmark_value in self.benchmarks.items():
            difference = carbon_intensity - benchmark_value
            percentage_diff = (difference / benchmark_value * 100) if benchmark_value > 0 else 0

            comparisons[benchmark_name] = {
                'value': benchmark_value,
                'difference': round(difference, 2),
                'percentage_difference': round(percentage_diff, 1),
                'status': 'better' if difference < 0 else 'worse'
            }

        return comparisons

    def _generate_insights(self, carbon_intensity: float, emissions: Dict) -> List[str]:
        """Generate actionable insights"""

        insights = []

        # Carbon intensity insights
        if carbon_intensity < self.benchmarks['best_in_class']:
            insights.append(
                f"🌟 Excellent! Carbon intensity ({carbon_intensity:.0f} kg/tonne) is better than best-in-class benchmark")
        elif carbon_intensity > self.benchmarks['india_average']:
            insights.append(
                f"⚠️ Carbon intensity ({carbon_intensity:.0f} kg/tonne) exceeds India average. Focus on efficiency improvements")

        # Emissions breakdown insights
        breakdown = emissions['breakdown_percent']
        if breakdown['fuel_combustion'] > 50:
            insights.append(
                "🔥 Fuel combustion is the largest emission source. Consider increasing alternative fuel rate")

        if breakdown['process_emissions'] > 45:
            insights.append("🏭 Process emissions are high. Explore clinker substitution strategies (slag, fly ash)")

        if breakdown['electricity'] > 20:
            insights.append(
                "⚡ Electrical consumption is significant. Optimize motor efficiency and consider waste heat recovery")

        # Add positive insight
        insights.append(
            f"💡 Current operation avoids {self._calculate_avoided_emissions(carbon_intensity):.0f} tonnes CO2/year vs India average")

        return insights

    def _calculate_avoided_emissions(self, current_intensity: float) -> float:
        """Calculate avoided emissions vs baseline"""

        annual_production = 285 * 24 * 330  # tonnes/h * hours/day * days/year
        baseline_intensity = self.benchmarks['india_average']

        avoided = (baseline_intensity - current_intensity) * annual_production / 1000
        return max(0, avoided)

    def _calculate_sustainability_score(self, emissions: Dict, carbon_intensity: float) -> Dict[str, Any]:
        """Calculate comprehensive sustainability score (0-100)"""

        scores = {}

        # 1. Carbon Intensity Score (35%)
        # Best: 550, Worst: 800
        ci_score = max(0, min(100, (800 - carbon_intensity) / (800 - 550) * 100))
        scores['carbon_intensity'] = round(ci_score, 1)

        # 2. Alternative Fuel Rate Score (25%)
        # Assume 30% AFR as baseline (would come from fuel optimizer)
        afr_score = 30 * 2  # Simplified: 30% AFR = 60 points
        scores['alternative_fuel_rate'] = round(min(100, afr_score), 1)

        # 3. Energy Efficiency Score (20%)
        # Based on specific energy consumption
        # Target: <95 kWh/tonne, Current estimate: ~100
        energy_score = max(0, min(100, (120 - 100) / (120 - 95) * 100))
        scores['energy_efficiency'] = round(energy_score, 1)

        # 4. Waste Heat Recovery Score (10%)
        # Estimate based on cooler efficiency
        whr_score = 70  # Placeholder
        scores['waste_heat_recovery'] = round(whr_score, 1)

        # 5. Circular Economy Score (10%)
        # Based on alternative raw materials usage
        ce_score = 50  # Placeholder
        scores['circular_economy'] = round(ce_score, 1)

        # Calculate weighted total
        total_score = sum(
            scores[key] * self.sustainability_weights[key]
            for key in scores
        )

        # Determine grade
        if total_score >= 90:
            grade = 'A+'
        elif total_score >= 80:
            grade = 'A'
        elif total_score >= 70:
            grade = 'B+'
        elif total_score >= 60:
            grade = 'B'
        elif total_score >= 50:
            grade = 'C'
        else:
            grade = 'D'

        return {
            'total_score': round(total_score, 1),
            'grade': grade,
            'component_scores': scores,
            'interpretation': self._interpret_score(total_score)
        }

    def _interpret_score(self, score: float) -> str:
        """Interpret sustainability score"""

        if score >= 80:
            return "Outstanding sustainability performance. Leading industry standards."
        elif score >= 70:
            return "Good sustainability practices. Above average performance."
        elif score >= 60:
            return "Moderate sustainability. Room for improvement in key areas."
        else:
            return "Sustainability improvement needed. Focus on emissions reduction strategies."

    async def calculate_monthly_report(self, month: int, year: int) -> Dict[str, Any]:
        """Generate comprehensive monthly sustainability report"""

        # Date range for the month
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(SensorReading).where(
                    SensorReading.timestamp >= start_date,
                    SensorReading.timestamp < end_date
                )
            )
            readings = result.scalars().all()

        if not readings:
            return {'error': 'No data for specified month'}

        # Calculate daily emissions
        daily_emissions = {}
        for reading in readings:
            day = reading.timestamp.date()
            if day not in daily_emissions:
                daily_emissions[day] = []
            daily_emissions[day].append(reading)

        # Aggregate monthly metrics
        total_emissions = 0
        total_production = 0
        daily_intensities = []

        for day, day_readings in daily_emissions.items():
            emissions = self._calculate_emissions_breakdown(day_readings)
            production = self._estimate_production_rate(day_readings) * 24  # Daily production

            total_emissions += emissions['total_kg_co2_per_hour'] * 24
            total_production += production

            if production > 0:
                daily_intensities.append(emissions['total_kg_co2_per_hour'] * 24 / production)

        avg_carbon_intensity = total_emissions / total_production if total_production > 0 else 0

        return {
            'month': f"{year}-{month:02d}",
            'summary': {
                'total_emissions_tonnes': round(total_emissions / 1000, 2),
                'total_production_tonnes': round(total_production, 2),
                'average_carbon_intensity': round(avg_carbon_intensity, 2),
                'best_day_intensity': round(min(daily_intensities), 2) if daily_intensities else 0,
                'worst_day_intensity': round(max(daily_intensities), 2) if daily_intensities else 0
            },
            'trends': {
                'intensity_trend': 'improving' if len(daily_intensities) > 1 and daily_intensities[-1] <
                                                  daily_intensities[0] else 'stable',
                'daily_variation_percent': round(np.std(daily_intensities) / np.mean(daily_intensities) * 100,
                                                 1) if daily_intensities else 0
            },
            'benchmark_comparison': self._compare_to_benchmarks(avg_carbon_intensity),
            'cost_of_carbon': self._calculate_carbon_cost(total_emissions),
            'recommendations': self._generate_monthly_recommendations(avg_carbon_intensity, daily_intensities)
        }

    def _calculate_carbon_cost(self, total_emissions_kg: float) -> Dict[str, float]:
        """Calculate cost of carbon emissions"""

        # Carbon price scenarios (USD per tonne CO2)
        scenarios = {
            'current_india': 0,  # No carbon tax currently
            'eu_ets': 85,
            'social_cost': 51,
            'paris_aligned': 120
        }

        emissions_tonnes = total_emissions_kg / 1000

        return {
            scenario: round(emissions_tonnes * price, 2)
            for scenario, price in scenarios.items()
        }

    def _generate_monthly_recommendations(
            self,
            avg_intensity: float,
            daily_intensities: List[float]
    ) -> List[str]:
        """Generate monthly recommendations"""

        recommendations = []

        # Variability check
        if daily_intensities:
            variability = np.std(daily_intensities) / np.mean(daily_intensities)
            if variability > 0.15:
                recommendations.append("High day-to-day variability detected. Focus on process stabilization")

        # Performance check
        if avg_intensity > self.benchmarks['india_average']:
            recommendations.append(
                "Carbon intensity above India average. Priority actions: increase AFR and optimize thermal efficiency")

        # Target alignment
        gap_to_target = avg_intensity - self.benchmarks['target_2030']
        if gap_to_target > 0:
            recommendations.append(f"Need to reduce intensity by {gap_to_target:.0f} kg/tonne to meet 2030 targets")

        # Positive reinforcement
        if avg_intensity < self.benchmarks['world_average']:
            recommendations.append("✅ Below world average! Continue current optimization strategies")

        return recommendations


# Global instance
carbon_tracker = CarbonFootprintTracker()