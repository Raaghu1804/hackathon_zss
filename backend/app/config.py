import os
from pydantic_settings import BaseSettings
from typing import Optional, Dict, List, ClassVar


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./cement_plant.db"

    # AI Services
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "AIzaSyBvIzIMpPcqUduNF6rSUL2o-ClYWO4GtTA")
    GOOGLE_EARTH_ENGINE_PROJECT: str = os.getenv("GEE_PROJECT", "cement-optimizer")

    # Public Data Sources
    PUBLIC_DATA_SOURCES: ClassVar[Dict[str, Dict]] = {
        "cpcb": {
            "base_url": "https://app.cpcbccr.com/ccr/api",
            "update_frequency_hours": 4,
            "requires_auth": False
        },
        "imd": {
            "base_url": "http://api.imd.gov.in/weather",
            "update_frequency_hours": 3,
            "requires_auth": True,
            "api_key_env": "IMD_API_KEY"
        },
        "coal_ministry": {
            "base_url": "https://coal.nic.in/api/v1",
            "update_frequency_days": 30,
            "requires_auth": False
        },
        "cea": {
            "base_url": "https://cea.nic.in/api",
            "update_frequency_hours": 24,
            "requires_auth": False
        },
        "satellite": {
            "providers": ["LANDSAT", "SENTINEL"],
            "update_frequency_days": 5,
            "resolution_meters": 30
        }
    }

    # Plant Configuration (Example for multiple plants)
    PLANT_CONFIGS: ClassVar[List[Dict]] = [
        {
            "plant_id": "PLANT_001",
            "name": "Demo Cement Plant",
            "location": {"lat": 23.0225, "lon": 72.5714},  # Ahmedabad
            "region": "Gujarat",
            "capacity_mtpa": 5.0,
            "cpcb_stations": ["GJ001", "GJ002"],
            "alternative_fuel_sources": ["rice_husk", "rdf", "biomass"]
        }
    ]

    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Simulation Settings
    SIMULATION_INTERVAL: int = 5  # seconds
    USE_PUBLIC_DATA: bool = True
    PUBLIC_DATA_REFRESH_INTERVAL: int = 300  # seconds (5 minutes)

    # Chemistry Constraints (Industry Standards)
    CHEMISTRY_CONSTRAINTS: ClassVar[Dict] = {
        "LSF": {"min": 0.92, "max": 0.98, "optimal": 0.95},
        "SM": {"min": 2.3, "max": 2.7, "optimal": 2.5},
        "AM": {"min": 1.0, "max": 2.5, "optimal": 1.5},
        "C3S": {"min": 50, "max": 70, "optimal": 60},  # %
        "C2S": {"min": 15, "max": 30, "optimal": 20},  # %
        "C3A": {"min": 5, "max": 15, "optimal": 8},  # %
        "C4AF": {"min": 8, "max": 15, "optimal": 12}  # %
    }

    # Process Optimization Targets
    OPTIMIZATION_TARGETS: ClassVar[Dict] = {
        "thermal_energy": {"target": 3.2, "unit": "GJ/tonne"},  # Target < 3.2
        "electrical_energy": {"target": 95, "unit": "kWh/tonne"},  # Target < 95
        "co2_emission": {"target": 850, "unit": "kg/tonne"},  # Target < 850
        "alternative_fuel_rate": {"target": 50, "unit": "%"},  # Target > 50%
        "clinker_factor": {"target": 0.75, "unit": "ratio"}  # Target < 0.75
    }

    # Sensor Optimal Ranges (Enhanced with tighter controls)
    PRECALCINER_RANGES: ClassVar[Dict] = {
        "temperature": {"min": 820, "max": 900, "optimal": 860, "unit": "°C"},
        "pressure": {"min": -5, "max": -2, "optimal": -3.5, "unit": "mbar"},
        "oxygen_level": {"min": 2.0, "max": 4.0, "optimal": 3.0, "unit": "%"},
        "co_level": {"min": 0, "max": 0.1, "optimal": 0.02, "unit": "%"},
        "nox_level": {"min": 0, "max": 800, "optimal": 400, "unit": "mg/Nm³"},
        "fuel_flow": {"min": 8, "max": 12, "optimal": 10, "unit": "t/h"},
        "feed_rate": {"min": 250, "max": 350, "optimal": 300, "unit": "t/h"},
        "tertiary_air_temp": {"min": 600, "max": 900, "optimal": 750, "unit": "°C"},
        "calcination_degree": {"min": 85, "max": 95, "optimal": 92, "unit": "%"},
        "residence_time": {"min": 3, "max": 7, "optimal": 5, "unit": "seconds"}
    }

    ROTARY_KILN_RANGES: ClassVar[Dict] = {
        "burning_zone_temp": {"min": 1400, "max": 1500, "optimal": 1450, "unit": "°C"},
        "back_end_temp": {"min": 800, "max": 1200, "optimal": 1000, "unit": "°C"},
        "shell_temp": {"min": 200, "max": 350, "optimal": 275, "unit": "°C"},
        "oxygen_level": {"min": 1.0, "max": 3.0, "optimal": 2.0, "unit": "%"},
        "nox_level": {"min": 0, "max": 1200, "optimal": 600, "unit": "mg/Nm³"},
        "co_level": {"min": 0, "max": 0.05, "optimal": 0.01, "unit": "%"},
        "kiln_speed": {"min": 3.0, "max": 5.0, "optimal": 4.0, "unit": "rpm"},
        "fuel_rate": {"min": 10, "max": 15, "optimal": 12.5, "unit": "t/h"},
        "clinker_exit_temp": {"min": 1100, "max": 1300, "optimal": 1200, "unit": "°C"},
        "secondary_air_temp": {"min": 600, "max": 1000, "optimal": 800, "unit": "°C"},
        "flame_length": {"min": 5, "max": 8, "optimal": 6.5, "unit": "D"},
        "coating_thickness": {"min": 200, "max": 400, "optimal": 300, "unit": "mm"}
    }

    CLINKER_COOLER_RANGES: ClassVar[Dict] = {
        "inlet_temp": {"min": 1100, "max": 1300, "optimal": 1200, "unit": "°C"},
        "outlet_temp": {"min": 100, "max": 150, "optimal": 125, "unit": "°C"},
        "secondary_air_temp": {"min": 600, "max": 1000, "optimal": 800, "unit": "°C"},
        "tertiary_air_temp": {"min": 600, "max": 900, "optimal": 750, "unit": "°C"},
        "grate_speed": {"min": 10, "max": 30, "optimal": 20, "unit": "strokes/min"},
        "undergrate_pressure": {"min": 40, "max": 80, "optimal": 60, "unit": "mbar"},
        "cooling_air_flow": {"min": 2.3, "max": 3.3, "optimal": 2.8, "unit": "kg/kg"},
        "bed_height": {"min": 500, "max": 800, "optimal": 650, "unit": "mm"},
        "cooler_efficiency": {"min": 75, "max": 85, "optimal": 80, "unit": "%"},
        "heat_recovery": {"min": 60, "max": 75, "optimal": 70, "unit": "%"}
    }

    # Alternative Fuel Configuration
    ALTERNATIVE_FUELS: ClassVar[Dict] = {
        "rice_husk": {
            "max_substitution": 30,  # %
            "preparation": "size_reduction",
            "feeding_system": "separate"
        },
        "rdf": {
            "max_substitution": 40,  # %
            "preparation": "shredding",
            "feeding_system": "main_burner"
        },
        "biomass": {
            "max_substitution": 25,  # %
            "preparation": "drying",
            "feeding_system": "calciner"
        },
        "tyre_chips": {
            "max_substitution": 20,  # %
            "preparation": "shredding",
            "feeding_system": "kiln_inlet"
        },
        "plastic_waste": {
            "max_substitution": 15,  # %
            "preparation": "densification",
            "feeding_system": "main_burner"
        }
    }

    # Machine Learning Configuration
    ML_CONFIG: ClassVar[Dict] = {
        "model_update_frequency_hours": 24,
        "min_training_samples": 1000,
        "validation_split": 0.2,
        "confidence_threshold": 0.85,
        "anomaly_detection_sensitivity": 0.95,
        "optimization_iterations": 50,
        "bayesian_optimization": {
            "n_initial_points": 10,
            "acquisition_function": "EI",  # Expected Improvement
            "xi": 0.01,  # Exploration-exploitation trade-off
            "kappa": 2.576  # UCB parameter
        }
    }

    # Alert Thresholds
    ALERT_THRESHOLDS: ClassVar[Dict] = {
        "temperature_deviation": 50,  # °C
        "pressure_deviation": 2,  # mbar
        "efficiency_drop": 5,  # %
        "quality_deviation": 3,  # MPa for compressive strength
        "emission_limit": 50,  # mg/Nm³ above norm
    }

    # Reporting Configuration
    REPORTING: ClassVar[Dict] = {
        "daily_report_time": "06:00",
        "shift_duration_hours": 8,
        "kpi_calculation_interval_minutes": 15,
        "data_retention_days": 90,
        "archive_after_days": 365
    }

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()