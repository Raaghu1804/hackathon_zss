# backend/app/services/alternative_fuel_optimizer.py

import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime
from scipy.optimize import linprog
import json
from app.services.gemini_service import gemini_service


class AlternativeFuelOptimizer:
    """Optimize alternative fuel mix for cost and sustainability"""

    def __init__(self):
        # Fuel properties (calorific value in MJ/kg, cost in $/GJ, CO2 in kg/GJ)
        self.fuel_database = {
            'coal': {
                'calorific_value': 25.5,
                'ash_content': 12.0,
                'cost_per_gj': 3.2,
                'co2_per_gj': 94.6,
                'availability': 'unlimited',
                'handling_difficulty': 'low'
            },
            'rice_husk': {
                'calorific_value': 16.2,
                'ash_content': 18.0,
                'cost_per_gj': 1.8,
                'co2_per_gj': 9.5,  # 90% biogenic
                'availability': 'seasonal',
                'handling_difficulty': 'medium',
                'availability_mt_year': 31400000  # India availability
            },
            'rdf': {  # Refuse Derived Fuel
                'calorific_value': 18.5,
                'ash_content': 15.0,
                'cost_per_gj': 0.5,
                'co2_per_gj': 37.8,  # 60% biogenic
                'availability': 'high',
                'handling_difficulty': 'medium',
                'availability_mt_year': 62000000
            },
            'biomass': {
                'calorific_value': 14.8,
                'ash_content': 8.0,
                'cost_per_gj': 2.1,
                'co2_per_gj': 4.7,  # 95% biogenic
                'availability': 'seasonal',
                'handling_difficulty': 'high'
            },
            'petcoke': {
                'calorific_value': 32.0,
                'ash_content': 4.0,
                'cost_per_gj': 2.8,
                'co2_per_gj': 102.0,
                'availability': 'high',
                'handling_difficulty': 'low'
            },
            'plastic_waste': {
                'calorific_value': 28.0,
                'ash_content': 10.0,
                'cost_per_gj': 0.8,
                'co2_per_gj': 50.0,
                'availability': 'medium',
                'handling_difficulty': 'high'
            }
        }

        self.seasonal_factors = {
            'rice_husk': {
                'Jan': 1.2, 'Feb': 1.0, 'Mar': 0.8, 'Apr': 0.5,
                'May': 0.3, 'Jun': 0.4, 'Jul': 0.6, 'Aug': 0.8,
                'Sep': 1.0, 'Oct': 1.2, 'Nov': 1.3, 'Dec': 1.2
            },
            'biomass': {
                'Jan': 0.7, 'Feb': 0.6, 'Mar': 0.5, 'Apr': 0.8,
                'May': 1.0, 'Jun': 1.2, 'Jul': 1.0, 'Aug': 0.9,
                'Sep': 0.8, 'Oct': 0.7, 'Nov': 0.6, 'Dec': 0.7
            }
        }

    async def optimize_fuel_mix(
            self,
            total_energy_required_gj: float,
            cost_priority: float = 0.5,  # 0-1, higher = prioritize cost over emissions
            max_alternative_fuel_rate: float = 0.65,  # Maximum 65% AFR
            quality_constraints: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Optimize fuel mix using linear programming"""

        if quality_constraints is None:
            quality_constraints = {
                'max_ash_content': 14.0,
                'min_calorific_value': 20.0
            }

        # Get current month for seasonal adjustments
        current_month = datetime.now().strftime('%b')

        # Available fuels
        fuels = list(self.fuel_database.keys())
        n_fuels = len(fuels)

        # Objective function: weighted combination of cost and emissions
        costs = [self.fuel_database[f]['cost_per_gj'] for f in fuels]
        emissions = [self.fuel_database[f]['co2_per_gj'] for f in fuels]

        # Normalize and weight
        max_cost = max(costs)
        max_emission = max(emissions)
        c = [
            cost_priority * (costs[i] / max_cost) +
            (1 - cost_priority) * (emissions[i] / max_emission)
            for i in range(n_fuels)
        ]

        # Constraints
        A_ub = []
        b_ub = []

        # 1. Ash content constraint
        ash_constraint = [self.fuel_database[f]['ash_content'] for f in fuels]
        A_ub.append(ash_constraint)
        b_ub.append(quality_constraints['max_ash_content'])

        # 2. Alternative fuel rate constraint (coal must be >= 35%)
        alt_fuel_constraint = [-1 if f == 'coal' else 1 for f in fuels]
        A_ub.append(alt_fuel_constraint)
        b_ub.append(max_alternative_fuel_rate)

        # 3. Individual fuel availability constraints
        for i, fuel in enumerate(fuels):
            constraint = [0] * n_fuels
            constraint[i] = 1
            A_ub.append(constraint)

            # Apply seasonal factors
            availability_factor = 1.0
            if fuel in self.seasonal_factors:
                availability_factor = self.seasonal_factors[fuel].get(current_month, 1.0)

            # Maximum fraction based on handling and availability
            if fuel == 'coal':
                max_fraction = 1.0
            elif self.fuel_database[fuel]['handling_difficulty'] == 'high':
                max_fraction = 0.25 * availability_factor
            elif self.fuel_database[fuel]['handling_difficulty'] == 'medium':
                max_fraction = 0.35 * availability_factor
            else:
                max_fraction = 0.45 * availability_factor

            b_ub.append(max_fraction)

        # Equality constraint: fractions sum to 1
        A_eq = [[1] * n_fuels]
        b_eq = [1]

        # Bounds: each fuel between 0 and 1
        bounds = [(0, 1) for _ in range(n_fuels)]

        # Solve optimization
        result = linprog(
            c,
            A_ub=A_ub,
            b_ub=b_ub,
            A_eq=A_eq,
            b_eq=b_eq,
            bounds=bounds,
            method='highs'
        )

        if not result.success:
            return {
                'success': False,
                'error': 'Optimization failed',
                'message': result.message
            }

        # Calculate detailed results
        fuel_mix = dict(zip(fuels, result.x))

        # Remove negligible contributions
        fuel_mix = {k: v for k, v in fuel_mix.items() if v > 0.01}

        # Calculate metrics
        total_cost = sum(
            fuel_mix[f] * self.fuel_database[f]['cost_per_gj'] for f in fuel_mix) * total_energy_required_gj
        total_emissions = sum(
            fuel_mix[f] * self.fuel_database[f]['co2_per_gj'] for f in fuel_mix) * total_energy_required_gj

        # Baseline (100% coal)
        baseline_cost = self.fuel_database['coal']['cost_per_gj'] * total_energy_required_gj
        baseline_emissions = self.fuel_database['coal']['co2_per_gj'] * total_energy_required_gj

        # Alternative fuel rate
        afr = (1 - fuel_mix.get('coal', 0)) * 100

        # Get AI recommendations
        recommendations = await self._get_gemini_recommendations(
            fuel_mix,
            total_energy_required_gj,
            current_month
        )

        return {
            'success': True,
            'optimal_mix': fuel_mix,
            'alternative_fuel_rate_percent': round(afr, 1),
            'energy_breakdown_gj': {
                fuel: round(fraction * total_energy_required_gj, 2)
                for fuel, fraction in fuel_mix.items()
            },
            'economics': {
                'total_cost_usd': round(total_cost, 2),
                'baseline_cost_usd': round(baseline_cost, 2),
                'cost_savings_usd': round(baseline_cost - total_cost, 2),
                'cost_savings_percent': round((baseline_cost - total_cost) / baseline_cost * 100, 1)
            },
            'environmental': {
                'total_co2_tonnes': round(total_emissions / 1000, 2),
                'baseline_co2_tonnes': round(baseline_emissions / 1000, 2),
                'co2_reduction_tonnes': round((baseline_emissions - total_emissions) / 1000, 2),
                'co2_reduction_percent': round((baseline_emissions - total_emissions) / baseline_emissions * 100, 1)
            },
            'quality_metrics': {
                'weighted_ash_content': round(sum(fuel_mix[f] * self.fuel_database[f]['ash_content'] for f in fuel_mix),
                                              2),
                'weighted_calorific_value': round(
                    sum(fuel_mix[f] * self.fuel_database[f]['calorific_value'] for f in fuel_mix), 2)
            },
            'recommendations': recommendations,
            'timestamp': datetime.utcnow().isoformat()
        }

    async def _get_gemini_recommendations(
            self,
            fuel_mix: Dict[str, float],
            total_energy_gj: float,
            current_month: str
    ) -> List[str]:
        """Get AI-powered recommendations for fuel mix optimization"""

        prompt = f"""
        As an alternative fuel optimization expert for cement plants, analyze this fuel mix:

        Current Mix:
        {json.dumps({f: f"{v * 100:.1f}%" for f, v in fuel_mix.items()}, indent=2)}

        Total Energy: {total_energy_gj} GJ
        Current Month: {current_month}

        Provide 3-5 specific, actionable recommendations to:
        1. Improve cost efficiency
        2. Increase alternative fuel rate
        3. Optimize for current season
        4. Enhance operational stability

        Format as JSON array of strings:
        ["recommendation 1", "recommendation 2", ...]
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
            print(f"Gemini recommendations error: {e}")
            return [
                "Increase rice husk proportion during harvest season (Oct-Jan)",
                "Monitor ash content closely with RDF usage above 20%",
                "Consider blending plastic waste with biomass for stable combustion"
            ]

    def calculate_monthly_savings(
            self,
            current_mix: Dict[str, float],
            optimized_mix: Dict[str, float],
            monthly_production_tonnes: float = 85500  # 285 t/h * 24h * 30d / 2.4 = 85,500t
    ) -> Dict[str, Any]:
        """Calculate monthly savings from optimized fuel mix"""

        # Energy per tonne of clinker: ~3.2 GJ/tonne
        energy_per_tonne = 3.2
        total_energy = monthly_production_tonnes * energy_per_tonne

        # Current costs and emissions
        current_cost = sum(
            current_mix.get(f, 0) * self.fuel_database[f]['cost_per_gj']
            for f in self.fuel_database
        ) * total_energy

        current_emissions = sum(
            current_mix.get(f, 0) * self.fuel_database[f]['co2_per_gj']
            for f in self.fuel_database
        ) * total_energy

        # Optimized costs and emissions
        optimized_cost = sum(
            optimized_mix.get(f, 0) * self.fuel_database[f]['cost_per_gj']
            for f in self.fuel_database
        ) * total_energy

        optimized_emissions = sum(
            optimized_mix.get(f, 0) * self.fuel_database[f]['co2_per_gj']
            for f in self.fuel_database
        ) * total_energy

        return {
            'monthly_savings_usd': round(current_cost - optimized_cost, 2),
            'annual_savings_usd': round((current_cost - optimized_cost) * 12, 2),
            'monthly_co2_reduction_tonnes': round((current_emissions - optimized_emissions) / 1000, 2),
            'annual_co2_reduction_tonnes': round((current_emissions - optimized_emissions) * 12 / 1000, 2),
            'roi_months': round(current_cost / (current_cost - optimized_cost),
                                1) if current_cost > optimized_cost else 0
        }


# Global instance
fuel_optimizer = AlternativeFuelOptimizer()