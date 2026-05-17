from __future__ import annotations

from urllib.parse import urlencode

import httpx

from job_finder.config import HimalayasConfig
from job_finder.models import JobPost, normalize_datetime


class HimalayasAdapter:
    name = "himalayas"
    base_url = "https://himalayas.app/jobs/api/search"

    def __init__(
        self,
        config: HimalayasConfig,
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
                for page in range(1, self.config.max_pages + 1):
                    params = {"q": term, "sort": "recent", "page": page}
                    response = await client.get(f"{self.base_url}?{urlencode(params)}")
                    response.raise_for_status()
                    payload = response.json()
                    page_jobs = payload.get("jobs", [])
                    if not page_jobs:
                        break
                    for item in page_jobs[: self.config.page_size]:
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
        location = self._format_location(item)
        return JobPost(
            source=self.name,
            source_id=str(item.get("guid") or ""),
            title=str(item.get("title") or "").strip(),
            company=str(item.get("companyName") or "").strip(),
            url=str(item.get("applicationLink") or "").strip(),
            location=location,
            remote=True,
            description=str(item.get("description") or item.get("excerpt") or ""),
            published_at=normalize_datetime(item.get("pubDate")),
            raw=item,
        )

    def _format_location(self, item: dict) -> str:
        restrictions = item.get("locationRestrictions") or []
        if not restrictions:
            return "Worldwide"
        locations = []
        for restriction in restrictions:
            if isinstance(restriction, dict):
                locations.append(str(restriction.get("name") or restriction.get("alpha2") or ""))
            else:
                locations.append(str(restriction))
        return ", ".join(location for location in locations if location)
