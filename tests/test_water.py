import pytest
from datetime import datetime, timezone, timedelta
from pydantic import ValidationError
from app.services.water_service import WaterService
from app.schemas.water import WaterAssessmentRequest, WaterReading


def test_water_assessment_normal():
    service = WaterService()
    req = WaterAssessmentRequest(
        location_id="loc_1",
        previous_reading_liters=1000,
        current_reading_liters=1100,
        days_between=1,
        household_size=4,
        baseline_daily_per_person_liters=50
    )
    # Usage: (1100-1000)/1 = 100/day. Per person: 100/4 = 25. 25/50 = 0.5 (normal)
    resp = service.assess_consumption(req)
    assert resp.status == "normal"
    assert resp.severity == "low"
    assert resp.usage_per_person_liters == 25.0
    assert resp.location_id == "loc_1"


def test_water_assessment_elevated():
    service = WaterService()
    # Baseline: 100 L/person. 4 people = 400 total baseline.
    # Daily usage: 520 L -> 130 L/person -> ratio = 1.30 (elevated: >= 1.25)
    req = WaterAssessmentRequest(
        location_id="loc_1",
        previous_reading_liters=1000,
        current_reading_liters=1520,
        days_between=1,
        household_size=4,
        baseline_daily_per_person_liters=100
    )
    resp = service.assess_consumption(req)
    assert resp.status == "elevated"
    assert resp.severity == "medium"
    assert resp.estimated_excess_liters == 120.0


def test_water_assessment_unusual():
    service = WaterService()
    # Baseline: 100 L/person. 4 people = 400 total baseline.
    # Daily usage: 680 L -> 170 L/person -> ratio = 1.70 (unusual: >= 1.50)
    req = WaterAssessmentRequest(
        location_id="loc_1",
        previous_reading_liters=1000,
        current_reading_liters=1680,
        days_between=1,
        household_size=4,
        baseline_daily_per_person_liters=100
    )
    resp = service.assess_consumption(req)
    assert resp.status == "unusual"
    assert resp.severity == "high"
    assert resp.estimated_excess_liters == 280.0


def test_water_assessment_critical():
    service = WaterService()
    req = WaterAssessmentRequest(
        location_id="loc_1",
        previous_reading_liters=1000,
        current_reading_liters=2000,
        days_between=1,
        household_size=1,
        baseline_daily_per_person_liters=100
    )
    # Usage: 1000/day. Per person: 1000. 1000/100 = 10 > 2.0 (critical)
    resp = service.assess_consumption(req)
    assert resp.status == "critical"
    assert resp.severity == "critical"
    assert resp.estimated_excess_liters == 900.0


def test_water_assessment_without_baseline():
    service = WaterService()
    # Default benchmark is 135 L/person.
    # Usage: 400 L / 4 = 100 L/person -> within standard benchmark (normal)
    req = WaterAssessmentRequest(
        location_id="loc_1",
        previous_reading_liters=1000,
        current_reading_liters=1400,
        days_between=1,
        household_size=4,
        baseline_daily_per_person_liters=None
    )
    resp = service.assess_consumption(req)
    assert resp.status == "normal"
    assert resp.estimated_excess_liters == 0.0


def test_water_validation_reading_order():
    # current_reading_liters < previous_reading_liters must raise ValueError
    with pytest.raises(ValidationError):
        WaterAssessmentRequest(
            location_id="loc_1",
            previous_reading_liters=1500,
            current_reading_liters=1000,
            days_between=1,
            household_size=2
        )


def test_water_validation_days_and_household():
    with pytest.raises(ValidationError):
        WaterAssessmentRequest(
            location_id="loc_1",
            previous_reading_liters=1000,
            current_reading_liters=1100,
            days_between=0,  # Must be > 0
            household_size=2
        )

    with pytest.raises(ValidationError):
        WaterAssessmentRequest(
            location_id="loc_1",
            previous_reading_liters=1000,
            current_reading_liters=1100,
            days_between=1,
            household_size=0  # Must be >= 1
        )


def test_water_calculate_average_daily_usage_single_location():
    service = WaterService()
    now = datetime(2026, 10, 1, 8, 0, tzinfo=timezone.utc)
    readings = [
        WaterReading(
            reading_id="r1",
            location_id="loc_1",
            timestamp=now,
            cumulative_reading_liters=1000.0,
            unit="liters"
        ),
        WaterReading(
            reading_id="r2",
            location_id="loc_1",
            timestamp=now + timedelta(days=2),
            cumulative_reading_liters=1600.0,
            unit="liters"
        ),
    ]
    # 600 liters over 2 days = 300 liters/day
    avg = service.calculate_average_daily_usage(readings)
    assert avg == 300.0


def test_water_calculate_average_daily_usage_multi_location():
    service = WaterService()
    now = datetime(2026, 10, 1, 8, 0, tzinfo=timezone.utc)
    readings = [
        # loc_1: 400 L over 2 days = 200 L/day
        WaterReading(
            reading_id="r1",
            location_id="loc_1",
            timestamp=now,
            cumulative_reading_liters=1000.0,
            unit="liters"
        ),
        WaterReading(
            reading_id="r2",
            location_id="loc_1",
            timestamp=now + timedelta(days=2),
            cumulative_reading_liters=1400.0,
            unit="liters"
        ),
        # loc_2: 600 L over 2 days = 300 L/day
        WaterReading(
            reading_id="r3",
            location_id="loc_2",
            timestamp=now,
            cumulative_reading_liters=5000.0,
            unit="liters"
        ),
        WaterReading(
            reading_id="r4",
            location_id="loc_2",
            timestamp=now + timedelta(days=2),
            cumulative_reading_liters=5600.0,
            unit="liters"
        ),
    ]
    # Total multi-location daily usage = 200 + 300 = 500 L/day
    avg = service.calculate_average_daily_usage(readings)
    assert avg == 500.0


def test_water_calculate_average_daily_usage_timezone_naive_aware():
    service = WaterService()
    # Ensure naive and aware datetimes do not throw TypeError
    r1 = WaterReading(
        reading_id="r1",
        location_id="loc_1",
        timestamp=datetime(2026, 10, 1, 8, 0),  # naive
        cumulative_reading_liters=1000.0,
        unit="liters"
    )
    r2 = WaterReading(
        reading_id="r2",
        location_id="loc_1",
        timestamp=datetime(2026, 10, 2, 8, 0, tzinfo=timezone.utc),  # aware
        cumulative_reading_liters=1300.0,
        unit="liters"
    )
    avg = service.calculate_average_daily_usage([r1, r2])
    assert avg == 300.0


def test_water_calculate_average_daily_usage_insufficient():
    service = WaterService()
    assert service.calculate_average_daily_usage([]) is None
    single = [
        WaterReading(
            reading_id="r1",
            location_id="loc_1",
            timestamp=datetime.now(timezone.utc),
            cumulative_reading_liters=1000.0,
            unit="liters"
        )
    ]
    assert service.calculate_average_daily_usage(single) is None
