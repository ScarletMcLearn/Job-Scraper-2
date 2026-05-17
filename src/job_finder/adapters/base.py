from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from job_finder.models import JobPost


class SourceAdapterError(RuntimeError):
    pass


class UnsupportedSourceError(SourceAdapterError):
    pass


class SkippedSourceAdapter:
    def __init__(self, name: str, reason: str) -> None:
        self.name = name
        self.reason = reason

    async def fetch(self) -> list[JobPost]:
        raise SourceAdapterError(self.reason)


class JobSourceAdapter(Protocol):
    name: str

    async def fetch(self) -> list[JobPost]:
        ...
