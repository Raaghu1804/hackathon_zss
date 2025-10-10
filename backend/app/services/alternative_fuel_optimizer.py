import numpy as np
from scipy.optimize import linprog, minimize
from typing import Dict, List, Tuple, Optional, Any  # FIXED: Added Any import
from datetime import datetime, timedelta
import pandas as pd
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
                'calorific_value': 30.0,
                'ash_content': 10,
                'moisture': 2,
                'cost_per_gj': 0.8,
                'co2_emission': 75.68,  # 20% reduction
                'availability': 'continuous',
                'handling_cost': 1.8,
                'zinc_content': 1.2  # %
            }
        }

        self.constraints = {
            'max_ash_content': 15,  # %
            'max_moisture': 12,  # %
            'min_calorific_value': 18,  # GJ/tonne
            'max_alternative_fuel_rate': 60  # %
        }

    def optimize_fuel_mix(self,
                          total_energy_required: float,  # GJ/hour
                          availability_constraints: Dict[str, float],  # tonnes available
                          quality_requirements: Optional[Dict[str, float]] = None,
                          environmental_targets: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Optimize fuel mix using linear programming

        Args:
            total_energy_required: Total energy needed (GJ/hour)
            availability_constraints: Available quantity for each fuel (tonnes)
            quality_requirements: Quality constraints (ash, moisture, etc.)
            environmental_targets: CO2 emission targets

        Returns:
            Optimized fuel mix with cost and emission metrics
        """
        try:
            fuels = list(self.fuel_properties.keys())
            n_fuels = len(fuels)

            # Objective: Minimize cost
            c = np.array([
                self.fuel_properties[fuel]['cost_per_gj'] +
                self.fuel_properties[fuel]['handling_cost'] / self.fuel_properties[fuel]['calorific_value']
                for fuel in fuels
            ])

            # Constraints
            A_eq = []
            b_eq = []
            A_ub = []
            b_ub = []

            # Energy requirement constraint (equality)
            energy_coeffs = [self.fuel_properties[fuel]['calorific_value'] for fuel in fuels]
            A_eq.append(energy_coeffs)
            b_eq.append(total_energy_required)

            # Quality constraints (inequality)
            if quality_requirements:
                # Ash content constraint
                if 'max_ash_content' in quality_requirements:
                    ash_coeffs = [
                        self.fuel_properties[fuel]['ash_content'] * self.fuel_properties[fuel]['calorific_value']
                        for fuel in fuels
                    ]
                    A_ub.append(ash_coeffs)
                    b_ub.append(quality_requirements['max_ash_content'] * total_energy_required)

                # Moisture constraint
                if 'max_moisture' in quality_requirements:
                    moisture_coeffs = [
                        self.fuel_properties[fuel]['moisture'] * self.fuel_properties[fuel]['calorific_value']
                        for fuel in fuels
                    ]
                    A_ub.append(moisture_coeffs)
                    b_ub.append(quality_requirements['max_moisture'] * total_energy_required)

            # Availability constraints
            for i, fuel in enumerate(fuels):
                if fuel in availability_constraints:
                    constraint = [0] * n_fuels
                    constraint[i] = 1
                    A_ub.append(constraint)
                    b_ub.append(availability_constraints[fuel])

            # Environmental constraints
            if environmental_targets and 'max_co2_kg_per_gj' in environmental_targets:
                co2_coeffs = [
                    self.fuel_properties[fuel]['co2_emission'] * self.fuel_properties[fuel]['calorific_value']
                    for fuel in fuels
                ]
                A_ub.append(co2_coeffs)
                b_ub.append(environmental_targets['max_co2_kg_per_gj'] * total_energy_required)

            # Bounds (non-negative quantities)
            bounds = [(0, None) for _ in range(n_fuels)]

            # Solve linear program
            result = linprog(
                c=c,
                A_eq=np.array(A_eq) if A_eq else None,
                b_eq=np.array(b_eq) if b_eq else None,
                A_ub=np.array(A_ub) if A_ub else None,
                b_ub=np.array(b_ub) if b_ub else None,
                bounds=bounds,
                method='highs'
            )

            if result.success:
                # Convert solution to fuel mix
                fuel_tonnes = dict(zip(fuels, result.x))

                # Calculate percentages
                total_tonnes = sum(result.x)
                fuel_mix = {fuel: (tonnes / total_tonnes * 100) if total_tonnes > 0 else 0
                            for fuel, tonnes in fuel_tonnes.items()}

                # Calculate mix properties
                mix_properties = self._calculate_mix_properties(
                    {fuel: tonnes / sum(result.x) if sum(result.x) > 0 else 0
                     for fuel, tonnes in fuel_tonnes.items()}
                )

                return {
                    'success': True,
                    'optimal_mix': {k: round(v, 2) for k, v in fuel_mix.items() if v > 0.1},
                    'fuel_quantities_tonnes': {k: round(v, 2) for k, v in fuel_tonnes.items() if v > 0.1},
                    'total_cost_per_hour': round(result.fun, 2),
                    'mix_properties': mix_properties,
                    'co2_reduction': self._calculate_co2_reduction(
                        {fuel: tonnes / sum(result.x) if sum(result.x) > 0 else 0
                         for fuel, tonnes in fuel_tonnes.items()}
                    ),
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
            'annual_co2_savings_tonnes': round(reduction_percentage * 0.01 * 850 * 350 * 24, 0)
        }

    def _generate_implementation_plan(self, fuel_mix: Dict[str, float]) -> List[Dict[str, Any]]:
        """Generate implementation plan for optimal fuel mix"""
        plan = []

        for fuel, fraction in fuel_mix.items():
            if fraction > 0.01:  # Only include significant fuels
                fuel_plan = {
                    'fuel': fuel,
                    'percentage': round(fraction, 2),
                    'daily_requirement_tonnes': round(fraction * 0.01 * 300, 2),
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
                               target_emission_reduction: float,  # % reduction
                               energy_required: float,
                               availability: Dict[str, float]) -> Dict[str, Any]:
        """Optimize specifically for emission reduction target"""

        coal_baseline = self.fuel_properties['coal']['co2_emission']
        target_emission = coal_baseline * (1 - target_emission_reduction / 100)

        environmental_targets = {'max_co2_kg_per_gj': target_emission}

        result = self.optimize_fuel_mix(
            energy_required,
            availability,
            self.constraints,
            environmental_targets
        )

        if result['success']:
            return result
        else:
            return {
                'success': False,
                'message': 'Cannot achieve target emission reduction with available fuels',
                'target_emission': target_emission,
                'recommendation': 'Increase alternative fuel availability or reduce emission target'
            }

    def seasonal_fuel_planning(self, annual_demand: float) -> Dict[str, Any]:
        """Plan fuel procurement considering seasonal availability"""

        seasonal_availability = {
            'Q1': {
                'rice_husk': 0.4,
                'biomass': 0.3,
                'rdf': 1.0,
                'coal': 1.0
            },
            'Q2': {
                'rice_husk': 0.1,
                'biomass': 0.2,
                'rdf': 1.0,
                'coal': 1.0
            },
            'Q3': {
                'rice_husk': 0.2,
                'biomass': 0.4,
                'rdf': 1.0,
                'coal': 1.0
            },
            'Q4': {
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

            result = self.optimize_fuel_mix(
                quarterly_energy / (90 * 24),
                {k: v * 1000 for k, v in availability.items()},
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
            ]) if quarterly_plans else 0
        }


# Global instance
alternative_fuel_optimizer = AlternativeFuelOptimizer()