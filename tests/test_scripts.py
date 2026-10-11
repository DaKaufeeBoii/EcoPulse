import pytest
from scripts.validate_datasets import validate_datasets
from scripts.seed_local import seed_local
from app.repositories import get_repository


def test_validate_datasets_script(capsys):
    validate_datasets("data/sample")
    captured = capsys.readouterr()
    assert "Validation successful!" in captured.out
    assert "Validated 10 air records." in captured.out
    assert "Validated 15 water records." in captured.out
    assert "Validated 15 waste records." in captured.out


def test_seed_local_script_and_reset(capsys):
    repo = get_repository()
    # Run seed_local with reset=True
    seed_local("data/sample", reset=True)
    captured = capsys.readouterr()
    assert "Repository cleared." in captured.out
    assert "Seeded 10 air, 15 water, and 15 waste records." in captured.out

    # Verify repository state
    assert len(repo.get_air_assessments()) == 10
    assert len(repo.get_water_readings()) == 15
    assert len(repo.get_waste_entries()) == 15

    # Run without reset: adds more records
    seed_local("data/sample", reset=False)
    assert len(repo.get_air_assessments()) == 20

    # Clean up after test
    repo.clear_all()
