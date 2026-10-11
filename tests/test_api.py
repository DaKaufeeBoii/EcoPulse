import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.repositories import get_repository


@pytest.fixture(autouse=True)
def clean_repository():
    repo = get_repository()
    repo.clear_all()
    yield
    repo.clear_all()


@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "EcoPulse"


@pytest.mark.asyncio
async def test_water_readings_and_summary_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Submit first reading
        r1 = await ac.post("/api/v1/water/readings", json={
            "location_id": "loc_100",
            "cumulative_reading_liters": 1000.0,
            "timestamp": "2026-10-01T08:00:00Z"
        })
        assert r1.status_code == 200
        reading1 = r1.json()
        assert reading1["location_id"] == "loc_100"
        assert reading1["reading_id"].startswith("reading_")

        # 2. Submit second reading (2 days later, +600 liters)
        r2 = await ac.post("/api/v1/water/readings", json={
            "location_id": "loc_100",
            "cumulative_reading_liters": 1600.0,
            "timestamp": "2026-10-03T08:00:00Z"
        })
        assert r2.status_code == 200

        # 3. Retrieve readings list
        list_res = await ac.get("/api/v1/water/readings?location_id=loc_100")
        assert list_res.status_code == 200
        assert len(list_res.json()) == 2

        # 4. Check summary
        summary_res = await ac.get("/api/v1/water/summary?location_id=loc_100")
        assert summary_res.status_code == 200
        summary = summary_res.json()
        assert summary["total_readings_count"] == 2
        assert summary["average_daily_usage_liters"] == 300.0
        assert summary["latest_reading"]["cumulative_reading_liters"] == 1600.0


@pytest.mark.asyncio
async def test_water_assessments_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "location_id": "loc_100",
            "previous_reading_liters": 1000.0,
            "current_reading_liters": 1100.0,
            "days_between": 1.0,
            "household_size": 4,
            "baseline_daily_per_person_liters": 50.0
        }
        res = await ac.post("/api/v1/water/assessments", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "normal"
        assert data["daily_usage_liters"] == 100.0

        # Retrieve assessments
        get_res = await ac.get("/api/v1/water/assessments?location_id=loc_100")
        assert get_res.status_code == 200
        assert len(get_res.json()) == 1


@pytest.mark.asyncio
async def test_water_leak_report_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "location_id": "loc_100",
            "area": "kitchen taps",
            "description": "continuous dripping",
            "observed_severity": "low"
        }
        res = await ac.post("/api/v1/water/reports", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["report_id"].startswith("leak_")
        assert data["status"] == "open"

        # List reports
        list_res = await ac.get("/api/v1/water/reports?location_id=loc_100")
        assert list_res.status_code == 200
        assert len(list_res.json()) == 1


@pytest.mark.asyncio
async def test_air_assessments_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "location_id": "loc_air",
            "aqi": 85,
            "source": "demo_sensor",
            "dominant_pollutant": "PM2.5"
        }
        res = await ac.post("/api/v1/air/assessments", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["category"] == "Moderate"
        assert data["dominant_pollutant"] == "PM2.5"

        list_res = await ac.get("/api/v1/air/assessments?location_id=loc_air")
        assert list_res.status_code == 200
        assert len(list_res.json()) == 1


@pytest.mark.asyncio
async def test_waste_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create recycling entry
        e1 = await ac.post("/api/v1/waste/entries", json={
            "location_id": "loc_waste",
            "category": "plastic",
            "quantity": 2.0,
            "unit": "kg",
            "disposal_method": "recycling"
        })
        assert e1.status_code == 200

        # Create landfill entry
        e2 = await ac.post("/api/v1/waste/entries", json={
            "location_id": "loc_waste",
            "category": "paper",
            "quantity": 2000.0,
            "unit": "g",
            "disposal_method": "landfill"
        })
        assert e2.status_code == 200

        # Retrieve entries list
        list_res = await ac.get("/api/v1/waste/entries?location_id=loc_waste")
        assert list_res.status_code == 200
        assert len(list_res.json()) == 2

        # Retrieve summary
        sum_res = await ac.get("/api/v1/waste/summary?location_id=loc_waste")
        assert sum_res.status_code == 200
        summary = sum_res.json()
        assert summary["total_entries_count"] == 2
        assert summary["total_quantity_kg"] == 4.0
        assert summary["recycling_rate_percentage"] == 50.0
