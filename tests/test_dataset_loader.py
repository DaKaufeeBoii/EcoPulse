import pytest
from app.data.dataset_loader import DatasetLoader

@pytest.fixture
def loader():
    return DatasetLoader("data/sample")

def test_load_all_records(loader):
    air = loader.load_air_observations()
    water = loader.load_water_readings()
    waste = loader.load_waste_entries()
    
    assert len(air) == 10
    assert len(water) == 15
    assert len(waste) == 15
