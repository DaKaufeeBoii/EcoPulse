import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.data.dataset_loader import DatasetLoader

def validate_datasets(data_dir: str):
    loader = DatasetLoader(data_dir)
    try:
        print("Validating Air Observations...")
        air = loader.load_air_observations()
        print(f"Validated {len(air)} air records.")

        print("Validating Water Readings...")
        water = loader.load_water_readings()
        print(f"Validated {len(water)} water records.")

        print("Validating Waste Entries...")
        waste = loader.load_waste_entries()
        print(f"Validated {len(waste)} waste records.")
        
        print("Validation successful!")
    except Exception as e:
        print(f"Validation failed: {e}")

if __name__ == "__main__":
    validate_datasets("data/sample")
