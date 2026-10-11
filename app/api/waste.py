from fastapi import APIRouter, Depends
from typing import Optional, List
from app.repositories import get_repository
from app.repositories.base import BaseRepository
from app.services.waste_service import WasteService
from app.schemas.waste import WasteEntryCreate, WasteEntry, WasteSummaryResponse

router = APIRouter(prefix="/api/v1/waste", tags=["Waste"])
waste_service = WasteService()


@router.post("/entries", response_model=WasteEntry)
def record_entry(entry_in: WasteEntryCreate, repo: BaseRepository = Depends(get_repository)):
    entry = waste_service.create_entry(entry_in)
    return repo.save_waste_entry(entry)


@router.get("/entries", response_model=List[WasteEntry])
def get_waste_entries(location_id: Optional[str] = None, repo: BaseRepository = Depends(get_repository)):
    return repo.get_waste_entries(location_id=location_id)


@router.get("/summary", response_model=WasteSummaryResponse)
def get_waste_summary(location_id: Optional[str] = None, repo: BaseRepository = Depends(get_repository)):
    entries = repo.get_waste_entries(location_id=location_id)
    return waste_service.summarize_entries(entries, location_id=location_id)
