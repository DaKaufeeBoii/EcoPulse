import pytest
from pydantic import ValidationError
from datetime import datetime, timezone
from app.services.waste_service import WasteService, SUGGESTIONS_BY_CATEGORY
from app.schemas.waste import WasteEntryCreate, WasteEntry


def test_waste_category_suggestions():
    service = WasteService()
    categories = ["plastic", "paper", "organic", "e-waste", "e_waste", "metal", "glass", "hazardous", "textile", "other"]
    for cat in categories:
        entry = service.create_entry(
            WasteEntryCreate(
                location_id="loc_1",
                category=cat,
                quantity=1.0,
                unit="kg",
                disposal_method="recycled"
            )
        )
        assert entry.suggestion is not None
        assert len(entry.suggestion) > 0
        assert entry.category == cat.lower()


def test_waste_normalize_to_kg():
    service = WasteService()

    # kg
    assert service.normalize_to_kg(5.0, "kg") == 5.0
    assert service.normalize_to_kg(2.5, "Kilograms") == 2.5

    # grams
    assert service.normalize_to_kg(500.0, "g") == 0.5
    assert service.normalize_to_kg(2500.0, "grams") == 2.5

    # lbs
    lbs_val = service.normalize_to_kg(10.0, "lbs")
    assert round(lbs_val, 3) == 4.536

    # tonnes
    assert service.normalize_to_kg(2.0, "tonne") == 2000.0

    # Unknown unit raises ValueError (never treated blindly as kg)
    with pytest.raises(ValueError, match="Cannot normalize unknown or non-mass unit"):
        service.normalize_to_kg(10.0, "items")

    with pytest.raises(ValueError, match="Cannot normalize unknown or non-mass unit"):
        service.normalize_to_kg(10.0, "liters")


def test_waste_summarize_entries_diversion_rate():
    service = WasteService()
    entries = [
        WasteEntry(
            entry_id="w1",
            location_id="loc_1",
            timestamp=datetime.now(timezone.utc),
            category="plastic",
            quantity=2.0,
            unit="kg",
            disposal_method="recycling",
            suggestion="recycle"
        ),
        WasteEntry(
            entry_id="w2",
            location_id="loc_1",
            timestamp=datetime.now(timezone.utc),
            category="organic",
            quantity=3000.0,
            unit="g",  # 3.0 kg
            disposal_method="composting",
            suggestion="compost"
        ),
        WasteEntry(
            entry_id="w3",
            location_id="loc_1",
            timestamp=datetime.now(timezone.utc),
            category="e_waste",
            quantity=1.0,
            unit="kg",
            disposal_method="authorized_collection",
            suggestion="e-waste station"
        ),
        WasteEntry(
            entry_id="w4",
            location_id="loc_1",
            timestamp=datetime.now(timezone.utc),
            category="other",
            quantity=4.0,
            unit="kg",
            disposal_method="landfill",
            suggestion="landfill"
        ),
    ]

    # Total: 2 + 3 + 1 + 4 = 10.0 kg
    # Diverted (recycling, composting, authorized_collection): 2 + 3 + 1 = 6.0 kg
    # Diversion / recycling rate = 6.0 / 10.0 = 60.0%
    summary = service.summarize_entries(entries, location_id="loc_1")
    assert summary.total_entries_count == 4
    assert summary.total_quantity_kg == 10.0
    assert summary.recycling_rate_percentage == 60.0
    assert "plastic" in summary.categories
    assert summary.categories["plastic"].total_quantity_kg == 2.0


def test_waste_recommendations_thresholds():
    service = WasteService()
    # High organic (> 10kg), High plastic (> 5kg), and low recycling rate (< 50%)
    entries = [
        WasteEntry(
            entry_id="w1",
            location_id="loc_1",
            timestamp=datetime.now(timezone.utc),
            category="organic",
            quantity=15.0,
            unit="kg",
            disposal_method="landfill",
            suggestion="compost"
        ),
        WasteEntry(
            entry_id="w2",
            location_id="loc_1",
            timestamp=datetime.now(timezone.utc),
            category="plastic",
            quantity=6.0,
            unit="kg",
            disposal_method="landfill",
            suggestion="recycle"
        ),
    ]
    summary = service.summarize_entries(entries)
    assert any("High organic volume" in r for r in summary.top_recommendations)
    assert any("reusable containers" in r for r in summary.top_recommendations)
    assert any("below 50%" in r for r in summary.top_recommendations)


def test_waste_schema_validation():
    # Invalid category
    with pytest.raises(ValidationError):
        WasteEntryCreate(
            location_id="loc_1",
            category="nuclear",
            quantity=1.0,
            disposal_method="recycling"
        )

    # Invalid disposal method
    with pytest.raises(ValidationError):
        WasteEntryCreate(
            location_id="loc_1",
            category="plastic",
            quantity=1.0,
            disposal_method="thrown_in_river"
        )

    # Quantity <= 0
    with pytest.raises(ValidationError):
        WasteEntryCreate(
            location_id="loc_1",
            category="plastic",
            quantity=0.0
        )
