from __future__ import annotations

from typing import TYPE_CHECKING

from job_finder.adapters.base import UnsupportedSourceError

if TYPE_CHECKING:
    from job_finder.models import JobPost


class LinkedinAuthorizedPlaceholderAdapter:
    name = "linkedin"

    async def fetch(self) -> list[JobPost]:
        msg = (
            "LinkedIn direct ingestion is disabled. Provide authorized LinkedIn API, "
            "licensed data, or exported data access before implementing this adapter."
        )
        raise UnsupportedSourceError(msg)
