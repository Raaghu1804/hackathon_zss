import numpy as np
from scipy.optimize import linprog, minimize
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import pandas as pd
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class AlternativeFuelOptimizer:
    """Optimizer for alternative fuel mix in cement production"""

    def __init__(self):
        self.fuel_properties = {
            'coal': {
                'calorific_value': 25.5,  # GJ/tonne
                'ash_content': 12,  # %
                'moisture': 5,  # %
                'cost_per_gj': 3.2,  # USD/GJ
                'co2_emission': 94.6,  # kg CO2/GJ
                'availability': 'unlimited',
                'handling_cost': 0.5  # USD/tonne
            },
            'rice_husk': {
                'calorific_value': 16.2,
                'ash_content': 18,
                'moisture': 10,
                'cost_per_gj': 1.8,
                'co2_emission': 9.46,  # 90% reduction (biogenic)
                'availability': 'seasonal',
                'handling_cost': 1.2,
                'preparation_required': True
            },
            'rdf': {  # Refuse Derived Fuel
                'calorific_value': 18.5,
                'ash_content': 15,
                'moisture': 20,
                'cost_per_gj': 0.5,
                'co2_emission': 37.84,  # 60% reduction
                'availability': 'continuous',
                'handling_cost': 2.0,
                'quality_variation': 'high'
            },
            'biomass': {
                'calorific_value': 14.8,
                'ash_content': 8,
                'moisture': 15,
                'cost_per_gj': 2.1,
                'co2_emission': 4.73,  # 95% reduction (biogenic)
                'availability': 'seasonal',
                'handling_cost': 1.5,
                'storage_requirements': 'covered'
            },
            'pet_coke': {
                'calorific_value': 32.5,
                'ash_content': 1,
                'moisture': 1,
                'cost_per_gj': 2.8,
                'co2_emission': 92.8,
                'availability': 'continuous',
                'handling_cost': 0.8,
                'sulfur_content': 4.5  # %
            },
            'tyre_chips': {
                'calorific_value': 28.0,
                'ash_content': 6,
                'moisture': 2,
                'cost_per_gj': 1.2,
                'co2_emission': 75.0,  # Partial biogenic
                'availability': 'continuous',
                'handling_cost': 1.8,
                'special_permit': True
            }
        }

        self.constraints = {
            'max_ash_content': 15,  # %
            'max_moisture': 12,  # %
            'min_calorific_value': 20,  # GJ/tonne average
            'max_alternative_fuel_rate': 50,  # %
            'max_sulfur_input': 2.5,  # %
            'min_flame_temperature': 1800  # °C
        }

    def optimize_fuel_mix(self,
                          total_energy_required: float,  # GJ/hour
                          availability_constraints: Dict[str, float],
                          quality_requirements: Dict[str, float],
                          environmental_targets: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Optimize fuel mix for cost, quality, and environmental objectives
        Uses linear programming for multi-objective optimization
        """

        fuels = list(self.fuel_properties.keys())
        n_fuels = len(fuels)

        # Decision variables: fuel fractions (0-1)
        # Objective: minimize cost
        c = [self.fuel_properties[f]['cost_per_gj'] for f in fuels]

        # Constraints matrices
        A_ub = []
        b_ub = []
        A_eq = []
        b_eq = []

        # Constraint 1: Fractions sum to 1
        A_eq.append([1] * n_fuels)
        b_eq.append(1)

        # Constraint 2: Availability constraints
        for i, fuel in enumerate(fuels):
            if fuel in availability_constraints:
                constraint_row = [0] * n_fuels
                constraint_row[i] = total_energy_required
                A_ub.append(constraint_row)
                b_ub.append(availability_constraints[fuel])

        # Constraint 3: Maximum ash content
        ash_constraint = [self.fuel_properties[f]['ash_content'] for f in fuels]
        A_ub.append(ash_constraint)
        b_ub.append(quality_requirements.get('max_ash_content', self.constraints['max_ash_content']))

        # Constraint 4: Maximum moisture content
        moisture_constraint = [self.fuel_properties[f]['moisture'] for f in fuels]
        A_ub.append(moisture_constraint)
        b_ub.append(quality_requirements.get('max_moisture', self.constraints['max_moisture']))

        # Constraint 5: Maximum alternative fuel rate
        alt_fuel_constraint = [1 if f != 'coal' else 0 for f in fuels]
        A_ub.append(alt_fuel_constraint)
        b_ub.append(self.constraints['max_alternative_fuel_rate'] / 100)

        # Constraint 6: Environmental targets (CO2 reduction)
        if environmental_targets and 'max_co2_kg_per_gj' in environmental_targets:
            co2_constraint = [self.fuel_properties[f]['co2_emission'] for f in fuels]
            A_ub.append(co2_constraint)
            b_ub.append(environmental_targets['max_co2_kg_per_gj'])

        # Bounds: fuel fractions between 0 and 1
        bounds = [(0, 1) for _ in range(n_fuels)]

        # Solve optimization
        try:
            result = linprog(
                c,
                A_ub=A_ub if A_ub else None,
                b_ub=b_ub if b_ub else None,
                A_eq=A_eq if A_eq else None,
                b_eq=b_eq if b_eq else None,
                bounds=bounds,
                method='highs'
            )

            if result.success:
                fuel_mix = dict(zip(fuels, result.x))

                # Calculate mix properties
                mix_properties = self._calculate_mix_properties(fuel_mix)

                # Calculate savings and impact
                coal_baseline_cost = total_energy_required * self.fuel_properties['coal']['cost_per_gj']
                optimized_cost = result.fun * total_energy_required

                return {
                    'success': True,
                    'optimal_mix': {k: round(v * 100, 2) for k, v in fuel_mix.items() if v > 0.01},
                    'mix_properties': mix_properties,
                    'total_cost_per_hour': optimized_cost,
                    'cost_savings_per_hour': coal_baseline_cost - optimized_cost,
                    'annual_savings': (coal_baseline_cost - optimized_cost) * 8760,
                    'alternative_fuel_rate': sum(v for k, v in fuel_mix.items() if k != 'coal') * 100,
                    'co2_reduction': self._calculate_co2_reduction(fuel_mix),
                    'implementation_plan': self._generate_implementation_plan(fuel_mix)
                }
            else:
                return {
                    'success': False,
                    'error': 'Optimization failed',
                    'message': result.message
                }

        except Exception as e:
            logger.error(f"Fuel optimization error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _calculate_mix_properties(self, fuel_mix: Dict[str, float]) -> Dict[str, float]:
        """Calculate properties of the fuel mix"""
        properties = {
            'weighted_calorific_value': 0,
            'weighted_ash_content': 0,
            'weighted_moisture': 0,
            'weighted_co2_emission': 0,
            'estimated_flame_temperature': 0
        }

        for fuel, fraction in fuel_mix.items():
            if fraction > 0:
                properties['weighted_calorific_value'] += fraction * self.fuel_properties[fuel]['calorific_value']
                properties['weighted_ash_content'] += fraction * self.fuel_properties[fuel]['ash_content']
                properties['weighted_moisture'] += fraction * self.fuel_properties[fuel]['moisture']
                properties['weighted_co2_emission'] += fraction * self.fuel_properties[fuel]['co2_emission']

        # Estimate flame temperature based on calorific value and moisture
        properties['estimated_flame_temperature'] = (
                1800 +
                (properties['weighted_calorific_value'] - 20) * 15 -
                properties['weighted_moisture'] * 10
        )

        return {k: round(v, 2) for k, v in properties.items()}

    def _calculate_co2_reduction(self, fuel_mix: Dict[str, float]) -> Dict[str, float]:
        """Calculate CO2 reduction compared to coal baseline"""
        coal_baseline = self.fuel_properties['coal']['co2_emission']
        mix_emission = sum(
            fraction * self.fuel_properties[fuel]['co2_emission']
            for fuel, fraction in fuel_mix.items()
        )

        reduction_percentage = ((coal_baseline - mix_emission) / coal_baseline) * 100

        return {
            'baseline_emission_kg_per_gj': coal_baseline,
            'mix_emission_kg_per_gj': round(mix_emission, 2),
            'reduction_percentage': round(reduction_percentage, 2),
            'annual_co2_savings_tonnes': round(reduction_percentage * 0.01 * 850 * 350 * 24, 0)  # Approximate
        }

    def _generate_implementation_plan(self, fuel_mix: Dict[str, float]) -> List[Dict[str, Any]]:
        """Generate implementation plan for optimal fuel mix"""
        plan = []

        for fuel, fraction in fuel_mix.items():
            if fraction > 0.01:  # Only include significant fuels
                fuel_plan = {
                    'fuel': fuel,
                    'percentage': round(fraction * 100, 2),
                    'daily_requirement_tonnes': round(fraction * 300, 2),  # Assuming 300 tonnes/day
                    'preparation_requirements': [],
                    'handling_considerations': [],
                    'storage_requirements': []
                }

                # Add fuel-specific requirements
                if fuel == 'rice_husk':
                    fuel_plan['preparation_requirements'] = [
                        'Install size reduction equipment',
                        'Ensure moisture control systems'
                    ]
                    fuel_plan['storage_requirements'] = [
                        'Covered storage area',
                        'Fire prevention systems'
                    ]
                elif fuel == 'rdf':
                    fuel_plan['preparation_requirements'] = [
                        'Quality screening system',
                        'Metal separation equipment'
                    ]
                    fuel_plan['handling_considerations'] = [
                        'Odor management',
                        'Consistent feed rate control'
                    ]
                elif fuel == 'tyre_chips':
                    fuel_plan['preparation_requirements'] = [
                        'Shredding equipment',
                        'Wire removal system'
                    ]
                    fuel_plan['handling_considerations'] = [
                        'Special environmental permits required',
                        'Emission monitoring for zinc'
                    ]

                plan.append(fuel_plan)

        return plan

    def optimize_for_emissions(self,
                               total_energy_required: float,
                               co2_target: float,  # kg CO2/GJ
                               availability_constraints: Dict[str, float]) -> Dict[str, Any]:
        """Optimize fuel mix specifically for CO2 emissions reduction"""

        fuels = list(self.fuel_properties.keys())

        # Objective: minimize CO2 emissions
        def objective(x):
            return sum(
                x[i] * self.fuel_properties[fuel]['co2_emission']
                for i, fuel in enumerate(fuels)
            )

        # Constraints
        constraints = [
            {'type': 'eq', 'fun': lambda x: sum(x) - 1},  # Sum to 1
            {'type': 'ineq', 'fun': lambda x: self.constraints['max_ash_content'] -
                                              sum(x[i] * self.fuel_properties[fuel]['ash_content'] for i, fuel in
                                                  enumerate(fuels))}
        ]

        # Add availability constraints
        for i, fuel in enumerate(fuels):
            if fuel in availability_constraints:
                max_fraction = availability_constraints[fuel] / total_energy_required
                constraints.append({
                    'type': 'ineq',
                    'fun': lambda x, i=i, max_f=max_fraction: max_f - x[i]
                })

        # Bounds
        bounds = [(0, 1) for _ in fuels]

        # Initial guess (equal distribution)
        x0 = [1 / len(fuels)] * len(fuels)

        # Optimize
        result = minimize(
            objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )

        if result.success:
            fuel_mix = dict(zip(fuels, result.x))
            mix_co2 = result.fun

            return {
                'success': True,
                'optimal_mix_for_emissions': {k: round(v * 100, 2) for k, v in fuel_mix.items() if v > 0.01},
                'achieved_emission': round(mix_co2, 2),
                'target_emission': co2_target,
                'target_achieved': mix_co2 <= co2_target,
                'co2_reduction': self._calculate_co2_reduction(fuel_mix)
            }
        else:
            return {
                'success': False,
                'message': 'Could not find optimal solution for emission target'
            }

    def seasonal_fuel_planning(self, annual_demand: float) -> Dict[str, Any]:
        """Plan fuel procurement considering seasonal availability"""

        seasonal_availability = {
            'Q1': {  # Jan-Mar
                'rice_husk': 0.4,  # Post-harvest season
                'biomass': 0.3,
                'rdf': 1.0,
                'coal': 1.0
            },
            'Q2': {  # Apr-Jun
                'rice_husk': 0.1,
                'biomass': 0.2,
                'rdf': 1.0,
                'coal': 1.0
            },
            'Q3': {  # Jul-Sep
                'rice_husk': 0.2,
                'biomass': 0.4,
                'rdf': 1.0,
                'coal': 1.0
            },
            'Q4': {  # Oct-Dec
                'rice_husk': 0.3,
                'biomass': 0.1,
                'rdf': 1.0,
                'coal': 1.0
            }
        }

        quarterly_plans = {}
        total_cost = 0
        total_co2 = 0

        for quarter, availability in seasonal_availability.items():
            quarterly_energy = annual_demand / 4

            # Optimize for each quarter
            result = self.optimize_fuel_mix(
                quarterly_energy / (90 * 24),  # Per hour
                {k: v * 1000 for k, v in availability.items()},  # Convert to tonnes
                self.constraints
            )

            if result['success']:
                quarterly_plans[quarter] = {
                    'fuel_mix': result['optimal_mix'],
                    'cost': result['total_cost_per_hour'] * 90 * 24,
                    'co2_emission': result['mix_properties']['weighted_co2_emission']
                }
                total_cost += quarterly_plans[quarter]['cost']
                total_co2 += quarterly_plans[quarter]['co2_emission'] * quarterly_energy

        return {
            'quarterly_plans': quarterly_plans,
            'annual_cost': total_cost,
            'annual_co2_emissions': total_co2,
            'average_alternative_fuel_rate': np.mean([
                sum(v for k, v in plan['fuel_mix'].items() if k != 'coal')
                for plan in quarterly_plans.values()
            ])
        }


# Global instance
alternative_fuel_optimizer = AlternativeFuelOptimizer()