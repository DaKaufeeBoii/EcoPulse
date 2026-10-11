from typing import Optional, List, Dict
from app.repositories.base import BaseRepository
from app.schemas.water import (
    WaterReading,
    WaterAssessmentResponse,
    WaterLeakReport,
)
from app.schemas.air import AirAssessmentResponse
from app.schemas.waste import WasteEntry


class InMemoryRepository(BaseRepository):
    def __init__(self):
        self.water_readings: List[WaterReading] = []
        self.water_assessments: List[WaterAssessmentResponse] = []
        self.water_assessments_locations: Dict[str, str] = {}  # assessment_id -> location_id
        self.leak_reports: List[WaterLeakReport] = []
        self.air_assessments: List[AirAssessmentResponse] = []
        self.waste_entries: List[WasteEntry] = []
        self.idempotency_records: Dict[str, str] = {}  # key -> reading_id

    def save_water_reading(self, reading: WaterReading, idempotency_key: Optional[str] = None) -> WaterReading:
        if idempotency_key:
            if idempotency_key in self.idempotency_records:
                existing_id = self.idempotency_records[idempotency_key]
                for r in self.water_readings:
                    if r.reading_id == existing_id:
                        return r
            self.idempotency_records[idempotency_key] = reading.reading_id

        self.water_readings.append(reading)
        return reading

    def get_water_readings(self, location_id: Optional[str] = None) -> List[WaterReading]:
        if location_id is None:
            return list(self.water_readings)
        return [r for r in self.water_readings if r.location_id == location_id]

    def save_water_assessment(
        self, assessment: WaterAssessmentResponse, location_id: Optional[str] = None
    ) -> WaterAssessmentResponse:
        loc = location_id or assessment.location_id
        if loc and not assessment.location_id:
            assessment.location_id = loc
        self.water_assessments.append(assessment)
        if loc:
            self.water_assessments_locations[assessment.assessment_id] = loc
        return assessment

    def get_water_assessments(self, location_id: Optional[str] = None) -> List[WaterAssessmentResponse]:
        if location_id is None:
            return list(self.water_assessments)
        return [
            a for a in self.water_assessments
            if self.water_assessments_locations.get(a.assessment_id) == location_id
            or a.location_id == location_id
        ]

    def save_leak_report(self, report: WaterLeakReport) -> WaterLeakReport:
        self.leak_reports.append(report)
        return report

    def get_leak_reports(self, location_id: Optional[str] = None) -> List[WaterLeakReport]:
        if location_id is None:
            return list(self.leak_reports)
        return [r for r in self.leak_reports if r.location_id == location_id]

    def save_air_assessment(self, assessment: AirAssessmentResponse) -> AirAssessmentResponse:
        self.air_assessments.append(assessment)
        return assessment

    def get_air_assessments(self, location_id: Optional[str] = None) -> List[AirAssessmentResponse]:
        if location_id is None:
            return list(self.air_assessments)
        return [a for a in self.air_assessments if a.location_id == location_id]

    def save_waste_entry(self, entry: WasteEntry) -> WasteEntry:
        self.waste_entries.append(entry)
        return entry

    def get_waste_entries(self, location_id: Optional[str] = None) -> List[WasteEntry]:
        if location_id is None:
            return list(self.waste_entries)
        return [e for e in self.waste_entries if e.location_id == location_id]

    def clear_all(self) -> None:
        self.water_readings.clear()
        self.water_assessments.clear()
        self.water_assessments_locations.clear()
        self.leak_reports.clear()
        self.air_assessments.clear()
        self.waste_entries.clear()
        self.idempotency_records.clear()
