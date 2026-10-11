from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class AirObservationCreate(BaseModel):
    location_id: str = Field(..., min_length=1, description="Location identifier")
    aqi: int = Field(..., ge=0, le=500, description="Air Quality Index value (0 to 500)")
    source: str = Field(..., min_length=1, description="Source of observation (e.g., CPCB, IoT sensor, station name)")
    dominant_pollutant: Optional[str] = Field(default=None, description="Dominant pollutant (e.g., PM2.5, PM10, NO2)")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("timestamp")
    @classmethod
    def ensure_utc(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc)


class AirAssessmentResponse(BaseModel):
    assessment_id: str
    location_id: str
    timestamp: datetime
    aqi: int
    source: str
    dominant_pollutant: Optional[str] = None
    category: str
    risk_level: str
    health_implications: str
    precautions: List[str]
