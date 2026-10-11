import pytest
from datetime import datetime, timezone
from app.repositories.memory import InMemoryRepository
from app.schemas.water import WaterReading, WaterAssessmentResponse, WaterLeakReport
from app.schemas.air import AirAssessmentResponse
from app.schemas.waste import WasteEntry


def test_memory_repository_water_readings_and_idempotency():
    repo = InMemoryRepository()
    reading = WaterReading(
        reading_id="r_001",
        location_id="loc_1",
        timestamp=datetime.now(timezone.utc),
        cumulative_reading_liters=100.0,
        unit="liters"
    )

    # First save with idempotency key
    saved1 = repo.save_water_reading(reading, idempotency_key="key_123")
    assert saved1.reading_id == "r_001"
    assert len(repo.get_water_readings()) == 1

    # Second save with same idempotency key but different reading object
    duplicate_reading = WaterReading(
        reading_id="r_002",
        location_id="loc_1",
        timestamp=datetime.now(timezone.utc),
        cumulative_reading_liters=200.0,
        unit="liters"
    )
    saved2 = repo.save_water_reading(duplicate_reading, idempotency_key="key_123")
    assert saved2.reading_id == "r_001"
    assert len(repo.get_water_readings()) == 1  # No duplicate added


def test_memory_repository_location_filtering():
    repo = InMemoryRepository()
    now = datetime.now(timezone.utc)

    # Water readings across two locations
    repo.save_water_reading(WaterReading(reading_id="r1", location_id="loc_1", timestamp=now, cumulative_reading_liters=100, unit="liters"))
    repo.save_water_reading(WaterReading(reading_id="r2", location_id="loc_2", timestamp=now, cumulative_reading_liters=200, unit="liters"))

    assert len(repo.get_water_readings()) == 2
    assert len(repo.get_water_readings(location_id="loc_1")) == 1
    assert repo.get_water_readings(location_id="loc_1")[0].reading_id == "r1"

    # Air assessments
    repo.save_air_assessment(AirAssessmentResponse(
        assessment_id="a1", location_id="loc_1", timestamp=now, aqi=40, source="s1",
        category="Good", risk_level="low", health_implications="Clean", precautions=[]
    ))
    repo.save_air_assessment(AirAssessmentResponse(
        assessment_id="a2", location_id="loc_2", timestamp=now, aqi=150, source="s2",
        category="Unhealthy for Sensitive Groups", risk_level="elevated", health_implications="Caution", precautions=[]
    ))
    assert len(repo.get_air_assessments()) == 2
    assert len(repo.get_air_assessments(location_id="loc_2")) == 1

    # Waste entries
    repo.save_waste_entry(WasteEntry(
        entry_id="w1", location_id="loc_1", timestamp=now, category="plastic",
        quantity=1.0, unit="kg", disposal_method="recycled", suggestion="recycle"
    ))
    assert len(repo.get_waste_entries(location_id="loc_1")) == 1
    assert len(repo.get_waste_entries(location_id="loc_2")) == 0

    # Leak reports
    repo.save_leak_report(WaterLeakReport(
        report_id="leak_1", location_id="loc_1", timestamp=now,
        area="taps", description="dripping tap", observed_severity="low", status="open"
    ))
    assert len(repo.get_leak_reports(location_id="loc_1")) == 1
    assert len(repo.get_leak_reports(location_id="loc_2")) == 0


def test_memory_repository_clear_all():
    repo = InMemoryRepository()
    now = datetime.now(timezone.utc)
    repo.save_water_reading(WaterReading(reading_id="r1", location_id="loc_1", timestamp=now, cumulative_reading_liters=100, unit="liters"))
    repo.save_air_assessment(AirAssessmentResponse(
        assessment_id="a1", location_id="loc_1", timestamp=now, aqi=40, source="s1",
        category="Good", risk_level="low", health_implications="Clean", precautions=[]
    ))

    assert len(repo.get_water_readings()) == 1
    assert len(repo.get_air_assessments()) == 1

    repo.clear_all()

    assert len(repo.get_water_readings()) == 0
    assert len(repo.get_air_assessments()) == 0
    assert len(repo.idempotency_records) == 0
