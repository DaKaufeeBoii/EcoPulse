from fastapi import APIRouter, Depends
from typing import Optional, List
from app.repositories import get_repository
from app.repositories.base import BaseRepository
from app.services.air_service import AirService
from app.schemas.air import AirObservationCreate, AirAssessmentResponse

router = APIRouter(prefix="/api/v1/air", tags=["Air"])
air_service = AirService()


@router.post("/assessments", response_model=AirAssessmentResponse)
def assess_aqi(observation_in: AirObservationCreate, repo: BaseRepository = Depends(get_repository)):
    assessment = air_service.classify_aqi(observation_in)
    return repo.save_air_assessment(assessment)


@router.get("/assessments", response_model=List[AirAssessmentResponse])
def get_air_assessments(location_id: Optional[str] = None, repo: BaseRepository = Depends(get_repository)):
    return repo.get_air_assessments(location_id=location_id)
