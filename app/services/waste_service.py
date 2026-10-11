import uuid
from datetime import datetime, timezone
from typing import List, Dict, Optional
from app.schemas.waste import (
    WasteEntryCreate,
    WasteEntry,
    WasteSummaryResponse,
    WasteCategorySummary,
)

SUGGESTIONS_BY_CATEGORY = {
    "plastic": "Segregate clean dry plastics (PET/HDPE) for municipal recycling. Rinse containers to avoid contamination.",
    "paper": "Keep dry and separate from wet waste; bundle cardboard and clean paper for pulping recyclers.",
    "organic": "Compost on-site or route to municipal wet-waste processing to reduce methane emissions.",
    "e-waste": "Deposit at certified e-waste drop-off stations. Do not mix with domestic solid waste.",
    "e_waste": "Deposit at certified e-waste drop-off stations. Do not mix with domestic solid waste.",
    "metal": "Clean cans and scrap metal; metals have near-infinite recyclability and high scrap value.",
    "glass": "Rinse glass containers; keep separate by color when possible to support bottle-to-bottle recycling.",
    "hazardous": "Isolate batteries and chemical products for scheduled hazardous household waste collections.",
    "textile": "Donate wearable textiles or direct clean scrap textiles to textile recycling facilities.",
    "other": "Sort mixed waste to identify any recyclable fractions before final disposal.",
}

DIVERTED_DISPOSAL_METHODS = {
    "recycled",
    "recycling",
    "composted",
    "composting",
    "donated",
    "authorized_collection",
}


class WasteService:
    @staticmethod
    def get_suggestion_for_category(category: str) -> str:
        return SUGGESTIONS_BY_CATEGORY.get(
            category.lower().strip(),
            "Segregate waste at source to maximize recovery and divert materials from landfills."
        )

    @classmethod
    def create_entry(cls, entry_in: WasteEntryCreate) -> WasteEntry:
        suggestion = cls.get_suggestion_for_category(entry_in.category)
        return WasteEntry(
            entry_id=f"waste_{uuid.uuid4().hex[:12]}",
            location_id=entry_in.location_id,
            timestamp=entry_in.timestamp or datetime.now(timezone.utc),
            category=entry_in.category,
            quantity=entry_in.quantity,
            unit=entry_in.unit,
            disposal_method=entry_in.disposal_method,
            notes=entry_in.notes,
            suggestion=suggestion,
        )

    @classmethod
    def normalize_to_kg(cls, quantity: float, unit: str) -> float:
        unit_clean = unit.lower().strip()
        if unit_clean in ("kg", "kilogram", "kilograms"):
            return quantity
        if unit_clean in ("g", "gram", "grams"):
            return quantity / 1000.0
        if unit_clean in ("lbs", "lb", "pound", "pounds"):
            return quantity * 0.453592
        if unit_clean in ("t", "tonne", "tonnes", "ton", "tons", "metric ton", "metric tons"):
            return quantity * 1000.0
        raise ValueError(
            f"Cannot normalize unknown or non-mass unit '{unit}' to kilograms. "
            "Supported units are kg, g, lbs, tonnes."
        )

    @classmethod
    def summarize_entries(cls, entries: List[WasteEntry], location_id: Optional[str] = None) -> WasteSummaryResponse:
        total_kg = 0.0
        recycled_kg = 0.0
        categories_map: Dict[str, WasteCategorySummary] = {}

        for entry in entries:
            # Safely normalize only known mass units to kg; never treat unknown units as kilograms
            try:
                weight_kg = cls.normalize_to_kg(entry.quantity, entry.unit)
            except ValueError:
                weight_kg = 0.0

            total_kg += weight_kg

            disposal_clean = entry.disposal_method.lower().strip()
            if disposal_clean in DIVERTED_DISPOSAL_METHODS:
                recycled_kg += weight_kg

            cat = entry.category
            if cat not in categories_map:
                categories_map[cat] = WasteCategorySummary(
                    category=cat,
                    total_quantity_kg=0.0,
                    entries_count=0
                )
            cat_summary = categories_map[cat]
            cat_summary.total_quantity_kg = round(cat_summary.total_quantity_kg + weight_kg, 2)
            cat_summary.entries_count += 1

        recycling_rate = round((recycled_kg / total_kg * 100.0), 1) if total_kg > 0 else 0.0

        recommendations = []
        if "organic" in categories_map and categories_map["organic"].total_quantity_kg > 10:
            recommendations.append("High organic volume: set up a localized compost bin to divert kitchen wet waste.")
        if "plastic" in categories_map and categories_map["plastic"].total_quantity_kg > 5:
            recommendations.append("Consider replacing single-use plastic packaging with reusable containers.")
        if recycling_rate < 50.0 and len(entries) > 0:
            recommendations.append("Current diversion rate is below 50%. Expand segregation into dedicated dry and wet bins.")
        if not recommendations:
            recommendations.append("Maintain good segregation discipline across paper, plastic, and wet fractions.")

        return WasteSummaryResponse(
            location_id=location_id,
            total_entries_count=len(entries),
            total_quantity_kg=round(total_kg, 2),
            categories=categories_map,
            recycling_rate_percentage=recycling_rate,
            top_recommendations=recommendations,
        )
