from __future__ import annotations

import httpx

from job_finder.config import LeverConfig
from job_finder.models import JobPost, normalize_datetime


class LeverAdapter:
    name = "lever"
    base_url = "https://api.lever.co/v0/postings"

    def __init__(
        self,
        config: LeverConfig,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.config = config
        self.client = client

    async def fetch(self) -> list[JobPost]:
        close_client = self.client is None
        client = self.client or httpx.AsyncClient(timeout=30.0, follow_redirects=True)
        try:
            jobs: list[JobPost] = []
            for company in self.config.companies:
                response = await client.get(
                    f"{self.base_url}/{company}",
                    params={"mode": "json"},
                )
                response.raise_for_status()
                payload = response.json()
                for item in payload:
                    jobs.append(self._parse_job(company, item))
            return jobs
        finally:
            if close_client:
                await client.aclose()

    def _parse_job(self, company: str, item: dict) -> JobPost:
        categories = item.get("categories") or {}
        description_parts = [
            item.get("description") or "",
            item.get("descriptionPlain") or "",
            item.get("additional") or "",
        ]
        for list_item in item.get("lists") or []:
            description_parts.append(str(list_item.get("content") or ""))

        return JobPost(
            source=self.name,
            source_id=str(item.get("id") or ""),
            title=str(item.get("text") or "").strip(),
            company=company,
            url=str(item.get("hostedUrl") or item.get("applyUrl") or "").strip(),
            location=str(categories.get("location") or "").strip(),
            remote=_looks_remote(categories.get("location")),
            description=" ".join(description_parts),
            published_at=normalize_datetime(item.get("createdAt")),
            raw=item,
        )


def _looks_remote(value: object) -> bool | None:
    if value is None:
        return None
    return "remote" in str(value).lower()
