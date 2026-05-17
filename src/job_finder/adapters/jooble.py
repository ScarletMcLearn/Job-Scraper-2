from __future__ import annotations

from typing import TYPE_CHECKING, Any

import httpx

from job_finder.models import JobPost, normalize_datetime

if TYPE_CHECKING:
    from job_finder.config import JoobleConfig


class JoobleAdapter:
    name = "jooble"
    base_url = "https://jooble.org/api"

    def __init__(
        self,
        config: JoobleConfig,
        api_key: str,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.config = config
        self.api_key = api_key
        self.client = client

    async def fetch(self) -> list[JobPost]:
        close_client = self.client is None
        client = self.client or httpx.AsyncClient(timeout=30.0, follow_redirects=True)
        try:
            jobs: list[JobPost] = []
            seen: set[str] = set()
            locations = self.config.locations or [""]
            for term in self.config.search_terms:
                for location in locations:
                    for page in range(1, self.config.max_pages + 1):
                        response = await client.post(
                            f"{self.base_url}/{self.api_key}",
                            json={
                                "keywords": term,
                                "location": location,
                                "page": page,
                                "ResultOnPage": self.config.results_per_page,
                                "companysearch": "false",
                            },
                        )
                        response.raise_for_status()
                        payload = response.json()
                        page_jobs = payload.get("jobs", [])
                        if not page_jobs:
                            break
                        for item in page_jobs:
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

    def _parse_job(self, item: dict[str, Any]) -> JobPost:
        location = str(item.get("location") or "").strip()
        description_parts = [
            str(item.get("snippet") or ""),
            str(item.get("salary") or ""),
            str(item.get("type") or ""),
            str(item.get("source") or ""),
        ]
        return JobPost(
            source=self.name,
            source_id=str(item.get("id") or item.get("link") or ""),
            title=str(item.get("title") or "").strip(),
            company=str(item.get("company") or "").strip(),
            url=str(item.get("link") or "").strip(),
            location=location,
            remote=_looks_remote(
                " ".join(
                    [
                        str(item.get("title") or ""),
                        location,
                        str(item.get("snippet") or ""),
                    ]
                )
            ),
            description=" ".join(part for part in description_parts if part),
            published_at=normalize_datetime(item.get("updated")),
            raw=item,
        )


def _looks_remote(value: str) -> bool | None:
    if not value:
        return None
    normalized = value.lower()
    if "remote" in normalized or "worldwide" in normalized or "work from home" in normalized:
        return True
    return None
