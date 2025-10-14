# backend/app/api/enhanced_endpoints.py
# Add these endpoints to your main.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.models.database import get_db
from app.services.predictive_maintenance import predictive_maintenance
from app.services.alternative_fuel_optimizer import fuel_optimizer
from app.services.carbon_footprint_tracker import carbon_tracker

router = APIRouter()


# ==================== PREDICTIVE MAINTENANCE ENDPOINTS ====================

@router.get("/api/maintenance/forecast/{unit}")
async def get_maintenance_forecast(
        unit: str,
        hours_ahead: int = Query(default=24, ge=1, le=168),
        db: AsyncSession = Depends(get_db)
):
    """
    Get predictive maintenance forecast for a unit

    Args:
        unit: precalciner, rotary_kiln, or clinker_cooler
        hours_ahead: Forecast horizon (1-168 hours)

    Returns:
        Predicted anomalies, maintenance scores, and recommendations
    """
    try:
        forecast = await predictive_maintenance.forecast_anomalies(unit, hours_ahead)
        return forecast
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/maintenance/dashboard")
async def get_maintenance_dashboard(db: AsyncSession = Depends(get_db)):
    """
    Get comprehensive maintenance dashboard for all units
    """
    try:
        units = ["precalciner", "rotary_kiln", "clinker_cooler"]
        forecasts = {}

        for unit in units:
            forecast = await predictive_maintenance.forecast_anomalies(unit, 72)
            forecasts[unit] = forecast

        # Aggregate critical items
        all_maintenance = []
        for unit, forecast in forecasts.items():
            if 'recommended_maintenance' in forecast:
                for item in forecast['recommended_maintenance']:
                    item['unit'] = unit
                    all_maintenance.append(item)

        # Sort by urgency
        urgency_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        all_maintenance.sort(key=lambda x: urgency_order.get(x.get('urgency', 'low'), 4))

        return {
            'unit_forecasts': forecasts,
            'critical_maintenance': all_maintenance[:10],
            'total_estimated_downtime_hours': sum(
                f.get('estimated_downtime_hours', 0) for f in forecasts.values()
            ),
            'total_cost_impact': sum(
                f.get('cost_impact', {}).get('total_cost_usd', 0) for f in forecasts.values()
            )
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ALTERNATIVE FUEL OPTIMIZATION ENDPOINTS ====================

@router.post("/api/fuel/optimize")
async def optimize_fuel_mix(
        total_energy_gj: float = Query(default=10000, gt=0),
        cost_priority: float = Query(default=0.5, ge=0, le=1),
        max_afr: float = Query(default=0.65, ge=0, le=0.8)
):
    """
    Optimize alternative fuel mix

    Args:
        total_energy_gj: Total energy requirement in GJ
        cost_priority: Priority weight for cost (0-1, higher = prioritize cost over emissions)
        max_afr: Maximum alternative fuel rate (0-0.8)

    Returns:
        Optimized fuel mix with cost and environmental metrics
    """
    try:
        result = await fuel_optimizer.optimize_fuel_mix(
            total_energy_required_gj=total_energy_gj,
            cost_priority=cost_priority,
            max_alternative_fuel_rate=max_afr
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/fuel/savings")
async def calculate_fuel_savings(
        monthly_production: float = Query(default=85500, gt=0)
):
    """
    Calculate savings from alternative fuel optimization

    Args:
        monthly_production: Monthly production in tonnes

    Returns:
        Monthly and annual savings projections
    """
    try:
        # Current mix (example: 100% coal baseline)
        current_mix = {'coal': 1.0}

        # Get optimized mix
        optimization = await fuel_optimizer.optimize_fuel_mix(
            total_energy_required_gj=monthly_production * 3.2,
            cost_priority=0.5,
            max_alternative_fuel_rate=0.65
        )

        if not optimization['success']:
            raise HTTPException(status_code=400, detail="Optimization failed")

        # Calculate savings
        savings = fuel_optimizer.calculate_monthly_savings(
            current_mix=current_mix,
            optimized_mix=optimization['optimal_mix'],
            monthly_production_tonnes=monthly_production
        )

        return {
            'current_mix': current_mix,
            'optimized_mix': optimization['optimal_mix'],
            'savings': savings,
            'alternative_fuel_rate': optimization['alternative_fuel_rate_percent']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/fuel/database")
async def get_fuel_database():
    """Get complete alternative fuel database with properties"""
    return {
        'fuels': fuel_optimizer.fuel_database,
        'seasonal_factors': fuel_optimizer.seasonal_factors,
        'current_month': datetime.now().strftime('%b')
    }


# ==================== CARBON FOOTPRINT TRACKING ENDPOINTS ====================

@router.get("/api/carbon/realtime")
async def get_realtime_carbon_footprint(
        unit: Optional[str] = Query(default=None)
):
    """
    Get real-time carbon footprint analysis

    Args:
        unit: Optional unit filter (precalciner, rotary_kiln, clinker_cooler)

    Returns:
        Real-time emissions breakdown, carbon intensity, and sustainability score
    """
    try:
        footprint = await carbon_tracker.calculate_real_time_footprint(unit)
        return footprint
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/carbon/monthly")
async def get_monthly_carbon_report(
        month: int = Query(default=None, ge=1, le=12),
        year: int = Query(default=None, ge=2020, le=2030)
):
    """
    Get comprehensive monthly carbon footprint report

    Args:
        month: Month (1-12), defaults to current month
        year: Year (2020-2030), defaults to current year

    Returns:
        Monthly emissions, trends, benchmarks, and recommendations
    """
    try:
        from datetime import datetime

        if month is None:
            month = datetime.now().month
        if year is None:
            year = datetime.now().year

        report = await carbon_tracker.calculate_monthly_report(month, year)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/carbon/sustainability-score")
async def get_sustainability_score():
    """Get current sustainability score and breakdown"""
    try:
        footprint = await carbon_tracker.calculate_real_time_footprint()

        if 'error' in footprint:
            raise HTTPException(status_code=404, detail=footprint['error'])

        return footprint['sustainability_score']
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/carbon/benchmarks")
async def get_carbon_benchmarks():
    """Get industry carbon intensity benchmarks"""
    return {
        'benchmarks': carbon_tracker.benchmarks,
        'emission_factors': carbon_tracker.emission_factors,
        'interpretation': {
            'world_average': 'Global cement industry average',
            'india_average': 'Indian cement industry average',
            'best_in_class': 'Top 10% performers globally',
            'european_standard': 'EU cement industry standard',
            'target_2030': 'Paris Agreement aligned target'
        }
    }


# ==================== COMPARATIVE ANALYTICS ENDPOINTS ====================

@router.get("/api/analytics/multi-plant-comparison")
async def compare_plant_performance(db: AsyncSession = Depends(get_db)):
    """
    Compare performance across multiple plants (simulated for demo)

    This endpoint simulates multi-plant data for demonstration purposes
    """
    try:
        # Get current plant performance
        current_footprint = await carbon_tracker.calculate_real_time_footprint()

        # Simulate other plants with variations
        plants_data = [
            {
                'plant_id': 'plant_001',
                'plant_name': 'Primary Plant (Current)',
                'location': 'Rajasthan',
                'carbon_intensity': current_footprint.get('carbon_intensity_kg_co2_per_tonne', 680),
                'production_rate': current_footprint.get('production_rate_tonnes_per_hour', 285),
                'sustainability_score': current_footprint.get('sustainability_score', {}).get('total_score', 72),
                'afr_percent': 30,
                'energy_kwh_per_tonne': 95
            },
            {
                'plant_id': 'plant_002',
                'plant_name': 'Plant North',
                'location': 'Punjab',
                'carbon_intensity': 695,
                'production_rate': 320,
                'sustainability_score': 68,
                'afr_percent': 25,
                'energy_kwh_per_tonne': 98
            },
            {
                'plant_id': 'plant_003',
                'plant_name': 'Plant South',
                'location': 'Tamil Nadu',
                'carbon_intensity': 640,
                'production_rate': 290,
                'sustainability_score': 78,
                'afr_percent': 45,
                'energy_kwh_per_tonne': 92
            },
            {
                'plant_id': 'plant_004',
                'plant_name': 'Plant West',
                'location': 'Gujarat',
                'carbon_intensity': 710,
                'production_rate': 275,
                'sustainability_score': 65,
                'afr_percent': 20,
                'energy_kwh_per_tonne': 102
            }
        ]

        # Add rankings
        sorted_by_ci = sorted(plants_data, key=lambda x: x['carbon_intensity'])
        sorted_by_score = sorted(plants_data, key=lambda x: x['sustainability_score'], reverse=True)

        for i, plant in enumerate(sorted_by_ci):
            plant['carbon_rank'] = i + 1

        for i, plant in enumerate(sorted_by_score):
            plant['sustainability_rank'] = i + 1

        return {
            'plants': plants_data,
            'aggregated_metrics': {
                'total_production': sum(p['production_rate'] for p in plants_data) * 24,
                'average_carbon_intensity': sum(p['carbon_intensity'] for p in plants_data) / len(plants_data),
                'average_sustainability_score': sum(p['sustainability_score'] for p in plants_data) / len(plants_data),
                'best_performer': sorted_by_score[0]['plant_name'],
                'most_improvement_needed': sorted_by_score[-1]['plant_name']
            },
            'insights': [
                f"Best carbon intensity: {sorted_by_ci[0]['plant_name']} at {sorted_by_ci[0]['carbon_intensity']} kg/tonne",
                f"Highest AFR: Plant South at 45% - best practice to replicate",
                f"Energy efficiency leader: Plant South at 92 kWh/tonne",
                "Consider knowledge transfer program from top performers"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/analytics/performance-trends")
async def get_performance_trends(
        days: int = Query(default=30, ge=1, le=90),
        db: AsyncSession = Depends(get_db)
):
    """
    Get performance trends over time

    Args:
        days: Number of days to analyze (1-90)
    """
    try:
        from datetime import datetime, timedelta
        import random

        # Generate trend data (in production, query from database)
        trends = {
            'dates': [],
            'carbon_intensity': [],
            'production_rate': [],
            'energy_efficiency': [],
            'sustainability_score': []
        }

        base_ci = 680
        for i in range(days):
            date = (datetime.now() - timedelta(days=days - i - 1)).strftime('%Y-%m-%d')
            trends['dates'].append(date)

            # Simulate improving trends
            improvement_factor = i / days * 0.1
            trends['carbon_intensity'].append(round(base_ci * (1 - improvement_factor) + random.uniform(-10, 10), 1))
            trends['production_rate'].append(round(285 + random.uniform(-15, 15), 1))
            trends['energy_efficiency'].append(round(95 - improvement_factor * 5 + random.uniform(-2, 2), 1))
            trends['sustainability_score'].append(round(70 + improvement_factor * 15 + random.uniform(-3, 3), 1))

        return {
            'period': f'Last {days} days',
            'trends': trends,
            'summary': {
                'carbon_intensity_change_percent': round(
                    (trends['carbon_intensity'][-1] - trends['carbon_intensity'][0]) / trends['carbon_intensity'][
                        0] * 100, 1),
                'production_change_percent': round(
                    (trends['production_rate'][-1] - trends['production_rate'][0]) / trends['production_rate'][0] * 100,
                    1),
                'sustainability_improvement': round(
                    trends['sustainability_score'][-1] - trends['sustainability_score'][0], 1)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== EXPORT THESE ROUTES ====================

def include_enhanced_routes(app):
    """Include all enhanced routes in the main app"""
    app.include_router(router, tags=["Enhanced Features"])