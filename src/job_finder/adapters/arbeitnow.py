from __future__ import annotations

from urllib.parse import urlencode

import httpx

from job_finder.config import ArbeitnowConfig
from job_finder.models import JobPost, normalize_datetime


class ArbeitnowAdapter:
    name = "arbeitnow"
    base_url = "https://www.arbeitnow.com/api/job-board-api"

    def __init__(
        self,
        config: ArbeitnowConfig,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.config = config
        self.client = client

    async def fetch(self) -> list[JobPost]:
        close_client = self.client is None
        client = self.client or httpx.AsyncClient(timeout=30.0, follow_redirects=True)
        try:
            jobs: list[JobPost] = []
            for page in range(1, self.config.max_pages + 1):
                response = await client.get(f"{self.base_url}?{urlencode({'page': page})}")
                response.raise_for_status()
                payload = response.json()
                for item in payload.get("data", []):
                    jobs.append(self._parse_job(item))
            return jobs
        finally:
            if close_client:
                await client.aclose()

    def _parse_job(self, item: dict) -> JobPost:
        tags = item.get("tags") or []
        remote = item.get("remote")
        location = str(item.get("location") or "").strip()
        if isinstance(tags, list) and any(str(tag).lower() == "remote" for tag in tags):
            remote = True
        return JobPost(
            source=self.name,
            source_id=str(item.get("slug") or item.get("id") or ""),
            title=str(item.get("title") or "").strip(),
            company=str(item.get("company_name") or "").strip(),
            url=str(item.get("url") or "").strip(),
            location=location,
            remote=bool(remote) if remote is not None else None,
            description=str(item.get("description") or ""),
            published_at=normalize_datetime(item.get("created_at")),
            raw=item,
        )
