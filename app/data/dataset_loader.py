import csv
import json
from datetime import datetime
from typing import List, Dict, Any, Union
from pathlib import Path
from pydantic import ValidationError

from app.schemas.water import WaterReadingCreate
from app.schemas.air import AirObservationCreate
from app.schemas.waste import WasteEntryCreate

class DatasetLoader:
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)

    def load_air_observations(self) -> List[AirObservationCreate]:
        path = self.data_dir / "air_observations.csv"
        observations = []
        with open(path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                observations.append(AirObservationCreate(
                    location_id=row['location_id'],
                    aqi=int(row['aqi']),
                    source=row['source'],
                    dominant_pollutant=row.get('prominent_pollutant') or row.get('dominant_pollutant'),
                    timestamp=datetime.fromisoformat(row['timestamp'])
                ))
        return observations

    def load_water_readings(self) -> List[WaterReadingCreate]:
        path = self.data_dir / "water_readings.csv"
        readings = []
        with open(path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                readings.append(WaterReadingCreate(
                    location_id=row['location_id'],
                    cumulative_reading_liters=float(row['cumulative_reading_liters']),
                    unit="liters", # Default to liters
                    timestamp=datetime.fromisoformat(row['timestamp'])
                ))
        return readings

    def load_waste_entries(self) -> List[WasteEntryCreate]:
        path = self.data_dir / "waste_entries.csv"
        entries = []
        with open(path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                entries.append(WasteEntryCreate(
                    location_id=row['location_id'],
                    category=row['category'],
                    quantity=float(row['quantity']),
                    unit=row['unit'],
                    disposal_method=row['disposal_method'],
                    timestamp=datetime.fromisoformat(row['timestamp'])
                ))
        return entries
