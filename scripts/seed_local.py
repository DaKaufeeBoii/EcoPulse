import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import uuid
import argparse
from app.data.dataset_loader import DatasetLoader
from app.repositories import get_repository
from app.schemas.water import WaterReading
from app.services.air_service import AirService
from app.services.waste_service import WasteService

def seed_local(data_dir: str, reset: bool = False):
    repo = get_repository()
    
    if reset:
        repo.clear_all()
        print("Repository cleared.")
    
    loader = DatasetLoader(data_dir)
    
    # Load and save air observations as assessments
    air = loader.load_air_observations()
    for obs in air:
        repo.save_air_assessment(AirService.classify_aqi(obs))
        
    # Load and save water readings as proper WaterReading domain models
    water = loader.load_water_readings()
    for reading_in in water:
        reading = WaterReading(
            reading_id=f"reading_{uuid.uuid4().hex[:12]}",
            location_id=reading_in.location_id,
            timestamp=reading_in.timestamp,
            cumulative_reading_liters=reading_in.cumulative_reading_liters,
            unit=reading_in.unit,
        )
        repo.save_water_reading(reading, idempotency_key=reading_in.idempotency_key)
    
    # Load and save waste entries
    waste = loader.load_waste_entries()
    for entry_in in waste:
        repo.save_waste_entry(WasteService.create_entry(entry_in))
        
    print(f"Seeded {len(air)} air, {len(water)} water, and {len(waste)} waste records.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data/sample")
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()
    seed_local(args.data_dir, args.reset)
