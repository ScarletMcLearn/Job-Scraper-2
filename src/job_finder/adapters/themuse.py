from __future__ import annotations

from typing import TYPE_CHECKING, Any

import httpx

from job_finder.models import JobPost, normalize_datetime

if TYPE_CHECKING:
    from collections.abc import Mapping

    from job_finder.config import TheMuseConfig

HTTP_BAD_REQUEST = 400


class TheMuseAdapter:
    name = "themuse"
    base_url = "https://www.themuse.com/api/public/jobs"

    def __init__(
        self,
        config: TheMuseConfig,
        api_key: str | None = None,
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
            categories = self.config.categories or [None]
            locations = self.config.locations or [None]
            for category in categories:
                for location in locations:
                    for page in range(self.config.max_pages):
                        params = _clean_params(
                            {
                                "page": page,
                                "category": category,
                                "location": location,
                                "api_key": self.api_key,
                            }
                        )
                        response = await client.get(self.base_url, params=params)
                        if response.status_code == HTTP_BAD_REQUEST:
                            break
                        response.raise_for_status()
                        payload = response.json()
                        page_jobs = payload.get("results", [])
                        if not page_jobs:
                            break
                        for item in page_jobs:
                            job = self._parse_job(item)
                            key = job.url or f"{job.source}:{job.source_id}"
                            if key in seen:
                                continue
                            seen.add(key)
                            jobs.append(job)
                        page_count = payload.get("page_count")
                        if isinstance(page_count, int) and page >= page_count - 1:
                            break
            return jobs
        finally:
            if close_client:
                await client.aclose()

    def _parse_job(self, item: dict[str, Any]) -> JobPost:
        company = item.get("company") or {}
        refs = item.get("refs") or {}
        locations = _names(item.get("locations"))
        categories = _names(item.get("categories"))
        levels = _names(item.get("levels"))
        description_parts = [
            str(item.get("contents") or ""),
            "Categories: " + ", ".join(categories) if categories else "",
            "Levels: " + ", ".join(levels) if levels else "",
        ]
        location = ", ".join(locations)
        return JobPost(
            source=self.name,
            source_id=str(item.get("id") or ""),
            title=str(item.get("name") or "").strip(),
            company=str(company.get("name") if isinstance(company, dict) else "").strip(),
            url=str(refs.get("landing_page") or item.get("url") or "").strip(),
            location=location,
            remote=_looks_remote(location),
            description=" ".join(part for part in description_parts if part),
            published_at=normalize_datetime(item.get("publication_date")),
            raw=item,
        )


def _clean_params(params: Mapping[str, str | int | None]) -> dict[str, str | int]:
    return {key: value for key, value in params.items() if value not in (None, "")}


def _names(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    names: list[str] = []
    for value in values:
        if isinstance(value, dict):
            name = str(value.get("name") or "").strip()
        else:
            name = str(value or "").strip()
        if name:
            names.append(name)
    return names


def _looks_remote(value: str) -> bool | None:
    if not value:
        return None
    normalized = value.lower()
    if "remote" in normalized or "flexible" in normalized:
        return True
    return None
