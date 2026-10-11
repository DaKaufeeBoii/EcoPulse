import pytest
from pydantic import ValidationError
from datetime import datetime, timezone
from app.services.air_service import AirService
from app.schemas.air import AirObservationCreate


def test_air_classification_bands():
    service = AirService()

    # Good: <= 50
    good = service.classify_aqi(AirObservationCreate(location_id="loc_1", aqi=35, source="sensor_1"))
    assert good.category == "Good"
    assert good.risk_level == "low"
    assert len(good.precautions) > 0

    # Moderate: 51 - 100
    mod = service.classify_aqi(AirObservationCreate(location_id="loc_1", aqi=75, source="sensor_1"))
    assert mod.category == "Moderate"
    assert mod.risk_level == "moderate"

    # Unhealthy for Sensitive Groups: 101 - 150
    sens = service.classify_aqi(AirObservationCreate(location_id="loc_1", aqi=125, source="sensor_1"))
    assert sens.category == "Unhealthy for Sensitive Groups"
    assert sens.risk_level == "elevated"

    # Unhealthy: 151 - 200
    unh = service.classify_aqi(AirObservationCreate(location_id="loc_1", aqi=175, source="sensor_1"))
    assert unh.category == "Unhealthy"
    assert unh.risk_level == "high"

    # Very Unhealthy: 201 - 300
    vunh = service.classify_aqi(AirObservationCreate(location_id="loc_1", aqi=250, source="sensor_1"))
    assert vunh.category == "Very Unhealthy"
    assert vunh.risk_level == "very_high"

    # Hazardous: > 300
    haz = service.classify_aqi(AirObservationCreate(location_id="loc_1", aqi=420, source="sensor_1"))
    assert haz.category == "Hazardous"
    assert haz.risk_level == "severe"


def test_air_dominant_pollutant_preserved():
    service = AirService()
    obs = AirObservationCreate(
        location_id="loc_2",
        aqi=160,
        source="cpcb_station",
        dominant_pollutant="PM2.5"
    )
    resp = service.classify_aqi(obs)
    assert resp.dominant_pollutant == "PM2.5"
    assert resp.location_id == "loc_2"
    assert resp.assessment_id.startswith("air_assess_")


def test_air_validation_bounds():
    # Valid boundaries: 0 and 500
    obs_min = AirObservationCreate(location_id="loc", aqi=0, source="sensor")
    assert obs_min.aqi == 0

    obs_max = AirObservationCreate(location_id="loc", aqi=500, source="sensor")
    assert obs_max.aqi == 500

    # Negative AQI is invalid
    with pytest.raises(ValidationError):
        AirObservationCreate(location_id="loc", aqi=-1, source="sensor")

    # AQI > 500 is invalid
    with pytest.raises(ValidationError):
        AirObservationCreate(location_id="loc", aqi=501, source="sensor")
