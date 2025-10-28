import asyncio
import httpx
import ee
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class PublicDataService:
    """Service for integrating public data sources for cement plant optimization"""

    def __init__(self):
        # Initialize Earth Engine
        try:
            ee.Initialize()
            self.ee_initialized = True
        except:
            self.ee_initialized = False
            logger.warning("Google Earth Engine not initialized")

        self.data_sources = {
            'cpcb': {
                'base_url': 'https://app.cpcbccr.com/ccr/api',
                'update_frequency': timedelta(hours=4)
            },
            'imd': {
                'base_url': 'http://api.imd.gov.in/weather',
                'update_frequency': timedelta(hours=3)
            },
            'coal_ministry': {
                'base_url': 'https://coal.nic.in/api/v1',
                'update_frequency': timedelta(days=30)
            }
        }
        self.cache = {}
        self.last_update = {}

    async def get_cpcb_air_quality(self, station_ids: List[str]) -> Dict[str, Any]:
        """Fetch air quality data from Central Pollution Control Board"""
        async with httpx.AsyncClient() as client:
            results = {}
            for station_id in station_ids:
                try:
                    response = await client.get(
                        f"{self.data_sources['cpcb']['base_url']}/station/{station_id}",
                        timeout=10.0
                    )
                    if response.status_code == 200:
                        data = response.json()
                        results[station_id] = {
                            'pm25': data.get('PM2.5'),
                            'pm10': data.get('PM10'),
                            'so2': data.get('SO2'),
                            'no2': data.get('NO2'),
                            'co': data.get('CO'),
                            'timestamp': datetime.utcnow()
                        }
                except Exception as e:
                    logger.error(f"Error fetching CPCB data for station {station_id}: {e}")
                    results[station_id] = None
            return results

    async def get_satellite_thermal_signature(self, lat: float, lon: float,
                                              days_back: int = 7) -> Dict[str, Any]:
        """Get thermal signature from satellite imagery using Google Earth Engine"""
        if not self.ee_initialized:
            return {'error': 'Earth Engine not initialized'}

        try:
            point = ee.Geometry.Point([lon, lat])
            start_date = (datetime.utcnow() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            end_date = datetime.utcnow().strftime('%Y-%m-%d')

            # Landsat 8 thermal band
            collection = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
                .filterDate(start_date, end_date) \
                .filterBounds(point) \
                .select(['ST_B10'])  # Surface temperature band

            # Get median temperature
            median_temp = collection.median()

            # Sample the temperature at the plant location
            temp_value = median_temp.sample(point, 30).first().get('ST_B10').getInfo()

            # Convert from Kelvin to Celsius
            temp_celsius = (temp_value * 0.00341802 + 149.0) - 273.15

            # Analyze temporal variations
            time_series = collection.map(lambda img: ee.Feature(
                point,
                {'temperature': img.select('ST_B10').reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=point.buffer(100),
                    scale=30
                ).get('ST_B10'),
                 'date': img.date().format('YYYY-MM-dd')
                 }
            )).getInfo()

            return {
                'median_temperature': temp_celsius,
                'time_series': time_series['features'],
                'location': {'lat': lat, 'lon': lon},
                'period': {'start': start_date, 'end': end_date}
            }
        except Exception as e:
            logger.error(f"Error fetching satellite data: {e}")
            return {'error': str(e)}

    async def get_weather_data(self, lat: float, lon: float) -> Dict[str, Any]:
        """Fetch weather data from India Meteorological Department"""
        async with httpx.AsyncClient() as client:
            try:
                # IMD API endpoint (example structure)
                response = await client.get(
                    f"{self.data_sources['imd']['base_url']}/current",
                    params={'lat': lat, 'lon': lon},
                    timeout=10.0
                )
                if response.status_code == 200:
                    data = response.json()
                    return {
                        'temperature': data.get('temperature'),
                        'humidity': data.get('humidity'),
                        'wind_speed': data.get('wind_speed'),
                        'wind_direction': data.get('wind_direction'),
                        'pressure': data.get('pressure'),
                        'rainfall': data.get('rainfall'),
                        'timestamp': datetime.utcnow()
                    }
            except Exception as e:
                logger.error(f"Error fetching weather data: {e}")
                return None

    async def get_alternative_fuel_availability(self, region: str) -> Dict[str, Any]:
        """Get alternative fuel availability data from agricultural statistics"""
        # This would connect to agricultural residue databases
        # For now, returning simulated data based on region
        fuel_data = {
            'rice_husk': {
                'availability_tonnes': np.random.uniform(1000, 5000),
                'price_per_tonne': np.random.uniform(2000, 3500),
                'calorific_value': 16.2,  # GJ/tonne
                'moisture_content': np.random.uniform(8, 12)
            },
            'agricultural_waste': {
                'availability_tonnes': np.random.uniform(2000, 8000),
                'price_per_tonne': np.random.uniform(1500, 2500),
                'calorific_value': 14.8,
                'moisture_content': np.random.uniform(10, 15)
            },
            'municipal_waste': {
                'availability_tonnes': np.random.uniform(3000, 10000),
                'price_per_tonne': np.random.uniform(500, 1500),
                'calorific_value': 18.5,
                'moisture_content': np.random.uniform(15, 25)
            },
            'biomass': {
                'availability_tonnes': np.random.uniform(1500, 6000),
                'price_per_tonne': np.random.uniform(2500, 4000),
                'calorific_value': 14.8,
                'moisture_content': np.random.uniform(12, 18)
            }
        }

        return {
            'region': region,
            'fuels': fuel_data,
            'timestamp': datetime.utcnow(),
            'forecast_days': 30
        }

    async def get_coal_prices(self) -> Dict[str, Any]:
        """Fetch coal price data from Coal Ministry"""
        # Simulated API call - in production, use actual Coal Ministry API
        return {
            'national_coal_index': np.random.uniform(2500, 3500),
            'grades': {
                'G1': {'price': 4500, 'gcv': 7000},
                'G2': {'price': 4200, 'gcv': 6700},
                'G3': {'price': 3900, 'gcv': 6400},
                'G4': {'price': 3600, 'gcv': 6100},
                'G5': {'price': 3300, 'gcv': 5800}
            },
            'imported_coal': {
                'indonesia': {'price': 85, 'gcv': 5500},  # USD/tonne
                'south_africa': {'price': 95, 'gcv': 6000}
            },
            'timestamp': datetime.utcnow()
        }

    async def aggregate_public_data(self, plant_config: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate all public data sources for a cement plant"""
        tasks = []

        # Create async tasks for parallel data fetching
        if plant_config.get('cpcb_stations'):
            tasks.append(self.get_cpcb_air_quality(plant_config['cpcb_stations']))

        if plant_config.get('location'):
            lat, lon = plant_config['location']['lat'], plant_config['location']['lon']
            tasks.append(self.get_satellite_thermal_signature(lat, lon))
            tasks.append(self.get_weather_data(lat, lon))

        if plant_config.get('region'):
            tasks.append(self.get_alternative_fuel_availability(plant_config['region']))

        tasks.append(self.get_coal_prices())

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process and structure results
        aggregated_data = {
            'plant_id': plant_config.get('plant_id'),
            'timestamp': datetime.utcnow(),
            'data_sources': {}
        }

        # Map results to data sources
        result_mapping = [
            ('air_quality', 0),
            ('satellite_thermal', 1),
            ('weather', 2),
            ('alternative_fuels', 3),
            ('coal_prices', 4 if len(results) > 4 else 3)
        ]

        for source_name, index in result_mapping:
            if index < len(results) and not isinstance(results[index], Exception):
                aggregated_data['data_sources'][source_name] = results[index]

        return aggregated_data

    def validate_data_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and score data quality from public sources"""
        quality_metrics = {
            'completeness': 0,
            'timeliness': 0,
            'consistency': 0,
            'accuracy_confidence': 0
        }

        # Check completeness
        total_fields = 0
        available_fields = 0
        for source, source_data in data.get('data_sources', {}).items():
            if source_data:
                total_fields += len(source_data)
                available_fields += sum(1 for v in source_data.values() if v is not None)

        quality_metrics['completeness'] = (available_fields / total_fields * 100) if total_fields > 0 else 0

        # Check timeliness
        current_time = datetime.utcnow()
        for source, source_data in data.get('data_sources', {}).items():
            if isinstance(source_data, dict) and 'timestamp' in source_data:
                age = (current_time - source_data['timestamp']).total_seconds() / 3600
                if age < 1:
                    quality_metrics['timeliness'] += 25
                elif age < 4:
                    quality_metrics['timeliness'] += 20
                elif age < 24:
                    quality_metrics['timeliness'] += 10

        # Overall quality score
        quality_metrics['overall_score'] = np.mean(list(quality_metrics.values()))

        return quality_metrics


# Global instance
public_data_service = PublicDataService()