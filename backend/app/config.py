# backend/app/config.py

import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./cement_plant.db"
    
    # Gemini API
    GEMINI_API_KEY: str = "AIzaSyBvIzIMpPcqUduNF6rSUL2o-ClYWO4GtTA"
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Simulation Settings
    SIMULATION_INTERVAL: int = 5  # seconds
    
    # Sensor Optimal Ranges
    PRECALCINER_RANGES = {
        "temperature": {"min": 820, "max": 900, "unit": "°C"},
        "pressure": {"min": -5, "max": -2, "unit": "mbar"},
        "oxygen_level": {"min": 2.0, "max": 4.0, "unit": "%"},
        "co_level": {"min": 0, "max": 0.1, "unit": "%"},
        "nox_level": {"min": 0, "max": 800, "unit": "mg/Nm³"},
        "fuel_flow": {"min": 8, "max": 12, "unit": "t/h"},
        "feed_rate": {"min": 250, "max": 350, "unit": "t/h"},
        "tertiary_air_temp": {"min": 600, "max": 900, "unit": "°C"},
        "calcination_degree": {"min": 85, "max": 95, "unit": "%"}
    }
    
    ROTARY_KILN_RANGES = {
        "burning_zone_temp": {"min": 1400, "max": 1500, "unit": "°C"},
        "back_end_temp": {"min": 800, "max": 1200, "unit": "°C"},
        "shell_temp": {"min": 200, "max": 350, "unit": "°C"},
        "oxygen_level": {"min": 1.0, "max": 3.0, "unit": "%"},
        "nox_level": {"min": 0, "max": 1200, "unit": "mg/Nm³"},
        "co_level": {"min": 0, "max": 0.05, "unit": "%"},
        "kiln_speed": {"min": 3.0, "max": 5.0, "unit": "rpm"},
        "fuel_rate": {"min": 10, "max": 15, "unit": "t/h"},
        "clinker_exit_temp": {"min": 1100, "max": 1300, "unit": "°C"},
        "secondary_air_temp": {"min": 600, "max": 1000, "unit": "°C"}
    }
    
    CLINKER_COOLER_RANGES = {
        "inlet_temp": {"min": 1100, "max": 1300, "unit": "°C"},
        "outlet_temp": {"min": 100, "max": 150, "unit": "°C"},
        "secondary_air_temp": {"min": 600, "max": 1000, "unit": "°C"},
        "tertiary_air_temp": {"min": 600, "max": 900, "unit": "°C"},
        "grate_speed": {"min": 10, "max": 30, "unit": "strokes/min"},
        "undergrate_pressure": {"min": 40, "max": 80, "unit": "mbar"},
        "cooling_air_flow": {"min": 2.3, "max": 3.3, "unit": "kg/kg"},
        "bed_height": {"min": 500, "max": 800, "unit": "mm"},
        "cooler_efficiency": {"min": 75, "max": 85, "unit": "%"}
    }
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()