from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from job_finder.models import JobPost


class SourceAdapterError(RuntimeError):
    pass


class UnsupportedSourceError(SourceAdapterError):
    pass


class JobSourceAdapter(ABC):
    name: str

    @abstractmethod
    async def fetch(self) -> list[JobPost]:
        raise NotImplementedError
