from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import urlencode

import httpx

from job_finder.models import JobPost, normalize_datetime

if TYPE_CHECKING:
    from job_finder.config import RemotiveConfig


class RemotiveAdapter:
    name = "remotive"
    base_url = "https://remotive.com/api/remote-jobs"

    def __init__(
        self,
        config: RemotiveConfig,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.config = config
        self.client = client

    async def fetch(self) -> list[JobPost]:
        close_client = self.client is None
        client = self.client or httpx.AsyncClient(timeout=30.0, follow_redirects=True)
        try:
            jobs: list[JobPost] = []
            seen: set[str] = set()
            for term in self.config.search_terms:
                response = await client.get(
                    f"{self.base_url}?{urlencode({'search': term})}"
                )
                response.raise_for_status()
                payload = response.json()
                for item in payload.get("jobs", []):
                    job = self._parse_job(item)
                    key = job.url or f"{job.source}:{job.source_id}"
                    if key in seen:
                        continue
                    seen.add(key)
                    jobs.append(job)
            return jobs
        finally:
            if close_client:
                await client.aclose()

    def _parse_job(self, item: dict) -> JobPost:
        return JobPost(
            source=self.name,
            source_id=str(item.get("id") or ""),
            title=str(item.get("title") or "").strip(),
            company=str(item.get("company_name") or "").strip(),
            url=str(item.get("url") or "").strip(),
            location=str(item.get("candidate_required_location") or "").strip(),
            remote=True,
            description=str(item.get("description") or ""),
            published_at=normalize_datetime(item.get("publication_date")),
            raw=item,
        )
