from __future__ import annotations

from job_finder.adapters.base import UnsupportedSourceError
from job_finder.models import JobPost


class LinkedinAuthorizedPlaceholderAdapter:
    name = "linkedin"

    async def fetch(self) -> list[JobPost]:
        raise UnsupportedSourceError(
            "LinkedIn direct ingestion is disabled. Provide authorized LinkedIn API, "
            "licensed data, or exported data access before implementing this adapter."
        )
