from typing import Optional
from app.core.config import settings
from app.repositories.base import BaseRepository
from app.repositories.memory import InMemoryRepository

_repo_instance: Optional[BaseRepository] = None


def get_repository() -> BaseRepository:
    global _repo_instance
    if _repo_instance is None:
        if settings.storage_backend.lower() == "dynamodb":
            from app.repositories.dynamodb import DynamoDBRepository
            _repo_instance = DynamoDBRepository()
        else:
            _repo_instance = InMemoryRepository()
    return _repo_instance


def set_repository(repo: BaseRepository) -> None:
    global _repo_instance
    _repo_instance = repo
