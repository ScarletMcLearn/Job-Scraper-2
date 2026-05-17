from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import urlencode

import httpx

from job_finder.models import JobPost, normalize_datetime

if TYPE_CHECKING:
    from job_finder.config import RemoteJobsOrgConfig


class RemoteJobsOrgAdapter:
    name = "remotejobs_org"
    base_url = "https://remotejobs.org/api/v1/jobs"

    def __init__(
        self,
        config: RemoteJobsOrgConfig,
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
                for page in range(self.config.max_pages):
                    params = {
                        "q": term,
                        "limit": self.config.limit,
                        "offset": page * self.config.limit,
                    }
                    response = await client.get(f"{self.base_url}?{urlencode(params)}")
                    response.raise_for_status()
                    payload = response.json()
                    page_jobs = payload.get("data", [])
                    if not page_jobs:
                        break
                    for item in page_jobs:
                        job = self._parse_job(item)
                        key = job.url or f"{job.source}:{job.source_id}"
                        if key in seen:
                            continue
                        seen.add(key)
                        jobs.append(job)
                    pagination = payload.get("pagination") or {}
                    if not pagination.get("has_more"):
                        break
            return jobs
        finally:
            if close_client:
                await client.aclose()

    def _parse_job(self, item: dict) -> JobPost:
        company = item.get("company") or {}
        category = item.get("category") or {}
        description_parts = [
            str(item.get("description") or ""),
            str(item.get("salary_text") or ""),
            str(item.get("type") or ""),
            str(category.get("name") or ""),
        ]
        return JobPost(
            source=self.name,
            source_id=str(item.get("id") or ""),
            title=str(item.get("title") or "").strip(),
            company=str(company.get("name") or "").strip(),
            url=str(item.get("url") or item.get("apply_url") or "").strip(),
            location=str(item.get("location") or "Remote").strip(),
            remote=True,
            description=" ".join(part for part in description_parts if part),
            published_at=normalize_datetime(item.get("posted_at")),
            raw=item,
        )
