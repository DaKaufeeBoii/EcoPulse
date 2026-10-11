from datetime import datetime, timezone
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, field_validator


ALLOWED_CATEGORIES = {
    "plastic",
    "paper",
    "organic",
    "e-waste",
    "e_waste",
    "metal",
    "glass",
    "hazardous",
    "textile",
    "other",
}

ALLOWED_DISPOSAL_METHODS = {
    "recycled",
    "recycling",
    "composted",
    "composting",
    "landfill",
    "incinerated",
    "donated",
    "special_handling",
    "authorized_collection",
    "unknown",
}


class WasteEntryCreate(BaseModel):
    location_id: str = Field(..., min_length=1, description="Location identifier")
    category: str = Field(..., description="Material category (e.g., plastic, paper, organic, e-waste, metal, glass, hazardous)")
    quantity: float = Field(..., gt=0, description="Quantity of waste logged (must be > 0)")
    unit: str = Field(default="kg", description="Unit of measurement (e.g. kg, g, lbs, items)")
    disposal_method: str = Field(default="recycled", description="Method of disposal")
    notes: Optional[str] = Field(default=None)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("timestamp")
    @classmethod
    def ensure_utc(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc)

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in ALLOWED_CATEGORIES:
            raise ValueError(f"Category '{v}' is invalid. Allowed: {sorted(list(ALLOWED_CATEGORIES))}")
        return clean

    @field_validator("disposal_method")
    @classmethod
    def validate_disposal(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in ALLOWED_DISPOSAL_METHODS:
            raise ValueError(f"Disposal method '{v}' is invalid. Allowed: {sorted(list(ALLOWED_DISPOSAL_METHODS))}")
        return clean


class WasteEntry(BaseModel):
    entry_id: str
    location_id: str
    timestamp: datetime
    category: str
    quantity: float
    unit: str
    disposal_method: str
    notes: Optional[str] = None
    suggestion: str


class WasteCategorySummary(BaseModel):
    category: str
    total_quantity_kg: float
    entries_count: int


class WasteSummaryResponse(BaseModel):
    location_id: Optional[str] = None
    total_entries_count: int
    total_quantity_kg: float
    categories: Dict[str, WasteCategorySummary]
    recycling_rate_percentage: float
    top_recommendations: List[str]
