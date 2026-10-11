from abc import ABC, abstractmethod
from typing import Optional, List
from app.schemas.water import (
    WaterReading,
    WaterAssessmentResponse,
    WaterLeakReport,
)
from app.schemas.air import AirAssessmentResponse
from app.schemas.waste import WasteEntry


class BaseRepository(ABC):
    @abstractmethod
    def save_water_reading(self, reading: WaterReading, idempotency_key: Optional[str] = None) -> WaterReading:
        pass

    @abstractmethod
    def get_water_readings(self, location_id: Optional[str] = None) -> List[WaterReading]:
        pass

    @abstractmethod
    def save_water_assessment(
        self, assessment: WaterAssessmentResponse, location_id: Optional[str] = None
    ) -> WaterAssessmentResponse:
        pass

    @abstractmethod
    def get_water_assessments(self, location_id: Optional[str] = None) -> List[WaterAssessmentResponse]:
        pass

    @abstractmethod
    def save_leak_report(self, report: WaterLeakReport) -> WaterLeakReport:
        pass

    @abstractmethod
    def get_leak_reports(self, location_id: Optional[str] = None) -> List[WaterLeakReport]:
        pass

    @abstractmethod
    def save_air_assessment(self, assessment: AirAssessmentResponse) -> AirAssessmentResponse:
        pass

    @abstractmethod
    def get_air_assessments(self, location_id: Optional[str] = None) -> List[AirAssessmentResponse]:
        pass

    @abstractmethod
    def save_waste_entry(self, entry: WasteEntry) -> WasteEntry:
        pass

    @abstractmethod
    def get_waste_entries(self, location_id: Optional[str] = None) -> List[WasteEntry]:
        pass

    @abstractmethod
    def clear_all(self) -> None:
        pass
