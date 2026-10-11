from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from app.repositories import get_repository
from app.repositories.base import BaseRepository
from app.services.water_service import WaterService
from app.schemas.water import (
    WaterReadingCreate,
    WaterReading,
    WaterAssessmentRequest,
    WaterAssessmentResponse,
    WaterLeakReportCreate,
    WaterLeakReport,
    WaterSummaryResponse,
)

router = APIRouter(prefix="/api/v1/water", tags=["Water"])
water_service = WaterService()


def _to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


@router.post("/readings", response_model=WaterReading)
def submit_reading(reading_in: WaterReadingCreate, repo: BaseRepository = Depends(get_repository)):
    reading = WaterReading(
        reading_id=f"reading_{uuid.uuid4().hex[:12]}",
        location_id=reading_in.location_id,
        timestamp=reading_in.timestamp,
        cumulative_reading_liters=reading_in.cumulative_reading_liters,
        unit=reading_in.unit,
    )
    return repo.save_water_reading(reading, idempotency_key=reading_in.idempotency_key)


@router.get("/readings", response_model=List[WaterReading])
def get_readings(location_id: Optional[str] = None, repo: BaseRepository = Depends(get_repository)):
    return repo.get_water_readings(location_id=location_id)


@router.post("/assessments", response_model=WaterAssessmentResponse)
def assess_consumption(req: WaterAssessmentRequest, repo: BaseRepository = Depends(get_repository)):
    assessment = water_service.assess_consumption(req)
    return repo.save_water_assessment(assessment, location_id=req.location_id)


@router.get("/assessments", response_model=List[WaterAssessmentResponse])
def get_assessments(location_id: Optional[str] = None, repo: BaseRepository = Depends(get_repository)):
    return repo.get_water_assessments(location_id=location_id)


@router.post("/reports", response_model=WaterLeakReport)
def report_leak(report_in: WaterLeakReportCreate, repo: BaseRepository = Depends(get_repository)):
    report = WaterLeakReport(
        report_id=f"leak_{uuid.uuid4().hex[:12]}",
        location_id=report_in.location_id,
        timestamp=datetime.now(timezone.utc),
        area=report_in.area,
        description=report_in.description,
        observed_severity=report_in.observed_severity,
    )
    return repo.save_leak_report(report)


@router.get("/reports", response_model=List[WaterLeakReport])
def get_reports(location_id: Optional[str] = None, repo: BaseRepository = Depends(get_repository)):
    return repo.get_leak_reports(location_id=location_id)


@router.get("/summary", response_model=WaterSummaryResponse)
def get_water_summary(location_id: Optional[str] = None, repo: BaseRepository = Depends(get_repository)):
    readings = repo.get_water_readings(location_id=location_id)
    assessments = repo.get_water_assessments(location_id=location_id)
    reports = repo.get_leak_reports(location_id=location_id)
    
    latest_reading = sorted(readings, key=lambda r: _to_utc(r.timestamp))[-1] if readings else None
    latest_assessment = sorted(assessments, key=lambda a: _to_utc(a.timestamp))[-1] if assessments else None
    
    avg_usage = water_service.calculate_average_daily_usage(readings)
    
    return WaterSummaryResponse(
        location_id=location_id,
        total_readings_count=len(readings),
        latest_reading=latest_reading,
        average_daily_usage_liters=avg_usage,
        active_leak_reports_count=len([r for r in reports if r.status == "open"]),
        latest_assessment=latest_assessment,
    )
