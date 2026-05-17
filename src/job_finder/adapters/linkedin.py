from __future__ import annotations

from typing import TYPE_CHECKING

from job_finder.adapters.base import UnsupportedSourceError

if TYPE_CHECKING:
    from job_finder.models import JobPost


class LinkedinAuthorizedPlaceholderAdapter:
    name = "linkedin"

    async def fetch(self) -> list[JobPost]:
        msg = (
            "LinkedIn scan ingestion is disabled. This project does not scrape "
            "LinkedIn pages; enable this source only after approved LinkedIn API "
            "access or licensed/exported job-data access is available."
        )
        raise UnsupportedSourceError(msg)
