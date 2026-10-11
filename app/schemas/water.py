from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field, model_validator, field_validator
import uuid


class WaterReadingCreate(BaseModel):
    location_id: str = Field(..., min_length=1, description="Identifier for property or meter location")
    cumulative_reading_liters: float = Field(..., ge=0, description="Total cumulative meter reading in liters")
    unit: str = Field(default="liters", description="Unit of measurement")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    idempotency_key: Optional[str] = Field(default=None, description="Optional key to prevent duplicate submissions")

    @field_validator("timestamp")
    @classmethod
    def ensure_utc(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc)


class WaterReading(BaseModel):
    reading_id: str
    location_id: str
    timestamp: datetime
    cumulative_reading_liters: float
    unit: str


class WaterAssessmentRequest(BaseModel):
    location_id: str = Field(..., min_length=1, description="Identifier for property or meter location")
    previous_reading_liters: float = Field(..., ge=0, description="Previous meter reading in liters")
    current_reading_liters: float = Field(..., ge=0, description="Current meter reading in liters")
    days_between: float = Field(..., gt=0, description="Number of days between readings (must be > 0)")
    household_size: int = Field(..., ge=1, description="Number of occupants in household (must be >= 1)")
    baseline_daily_per_person_liters: Optional[float] = Field(
        default=None, ge=0, description="Optional baseline daily usage per person in liters"
    )

    @model_validator(mode="after")
    def validate_reading_order(self):
        if self.current_reading_liters < self.previous_reading_liters:
            raise ValueError(
                f"Current reading ({self.current_reading_liters}) cannot be lower than previous reading ({self.previous_reading_liters})"
            )
        return self


class WaterAssessmentResponse(BaseModel):
    assessment_id: str
    location_id: Optional[str] = None
    timestamp: datetime
    daily_usage_liters: float
    usage_per_person_liters: float
    status: str = Field(..., description="Classification status: normal, elevated, unusual, critical")
    severity: str = Field(..., description="Severity level: low, medium, high, critical")
    estimated_excess_liters: float = Field(
        default=0.0, description="Excess liters compared to baseline (0.0 if no baseline or usage is normal)"
    )
    explanation: str
    recommendation: str


class WaterLeakReportCreate(BaseModel):
    location_id: str = Field(..., min_length=1)
    area: str = Field(..., min_length=1, description="Area suspected (e.g. taps, pipes, toilet, tank, meter, other)")
    description: str = Field(..., min_length=1, description="Description of leak or dampness observed")
    observed_severity: str = Field(default="medium", description="Reported severity: low, medium, high, critical")
    reporter_contact: Optional[str] = Field(default=None)


class WaterLeakReport(BaseModel):
    report_id: str
    location_id: str
    timestamp: datetime
    area: str
    description: str
    observed_severity: str
    status: str = "open"


class WaterSummaryResponse(BaseModel):
    location_id: Optional[str] = None
    total_readings_count: int
    latest_reading: Optional[WaterReading] = None
    average_daily_usage_liters: Optional[float] = None
    active_leak_reports_count: int
    latest_assessment: Optional[WaterAssessmentResponse] = None
