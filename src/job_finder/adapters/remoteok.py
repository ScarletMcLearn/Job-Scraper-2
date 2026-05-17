from __future__ import annotations

import httpx

from job_finder.config import RemoteOkConfig
from job_finder.models import JobPost, normalize_datetime


class RemoteOkAdapter:
    name = "remoteok"
    base_url = "https://remoteok.com/api"

    def __init__(
        self,
        config: RemoteOkConfig,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.config = config
        self.client = client

    async def fetch(self) -> list[JobPost]:
        close_client = self.client is None
        client = self.client or httpx.AsyncClient(timeout=30.0, follow_redirects=True)
        try:
            response = await client.get(
                self.base_url,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "job-finder/0.1 (+https://remoteok.com/api)",
                },
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, list):
                return []

            jobs: list[JobPost] = []
            seen: set[str] = set()
            for item in payload:
                if not isinstance(item, dict) or not item.get("position"):
                    continue
                job = self._parse_job(item)
                key = job.url or f"{job.source}:{job.source_id}"
                if key in seen:
                    continue
                seen.add(key)
                jobs.append(job)
                if self.config.max_results > 0 and len(jobs) >= self.config.max_results:
                    break
            return jobs
        finally:
            if close_client:
                await client.aclose()

    def _parse_job(self, item: dict) -> JobPost:
        tags = item.get("tags") or []
        description_parts = [str(item.get("description") or "")]
        if isinstance(tags, list) and tags:
            description_parts.append("Tags: " + ", ".join(str(tag) for tag in tags))

        return JobPost(
            source=self.name,
            source_id=str(item.get("id") or item.get("slug") or ""),
            title=str(item.get("position") or "").strip(),
            company=str(item.get("company") or "").strip(),
            url=str(item.get("url") or item.get("apply_url") or "").strip(),
            location=str(item.get("location") or "Remote").strip(),
            remote=True,
            description=" ".join(part for part in description_parts if part),
            published_at=normalize_datetime(item.get("date") or item.get("epoch")),
            raw=item,
        )
