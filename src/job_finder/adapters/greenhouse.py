from __future__ import annotations

import httpx

from job_finder.config import GreenhouseConfig
from job_finder.models import JobPost, normalize_datetime


class GreenhouseAdapter:
    name = "greenhouse"
    base_url = "https://boards-api.greenhouse.io/v1/boards"

    def __init__(
        self,
        config: GreenhouseConfig,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.config = config
        self.client = client

    async def fetch(self) -> list[JobPost]:
        close_client = self.client is None
        client = self.client or httpx.AsyncClient(timeout=30.0, follow_redirects=True)
        try:
            jobs: list[JobPost] = []
            for board_token in self.config.board_tokens:
                response = await client.get(
                    f"{self.base_url}/{board_token}/jobs",
                    params={"content": "true"},
                )
                response.raise_for_status()
                payload = response.json()
                for item in payload.get("jobs", []):
                    jobs.append(self._parse_job(board_token, item))
            return jobs
        finally:
            if close_client:
                await client.aclose()

    def _parse_job(self, board_token: str, item: dict) -> JobPost:
        location = item.get("location") or {}
        return JobPost(
            source=self.name,
            source_id=str(item.get("id") or ""),
            title=str(item.get("title") or "").strip(),
            company=board_token,
            url=str(item.get("absolute_url") or "").strip(),
            location=str(location.get("name") or "").strip(),
            remote=None,
            description=str(item.get("content") or ""),
            published_at=normalize_datetime(item.get("updated_at")),
            raw=item,
        )
