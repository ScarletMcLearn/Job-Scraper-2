from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from job_finder.models import JobPost


class SourceAdapterError(RuntimeError):
    pass


class UnsupportedSourceError(SourceAdapterError):
    pass


class JobSourceAdapter(Protocol):
    name: str

    async def fetch(self) -> list[JobPost]:
        ...
