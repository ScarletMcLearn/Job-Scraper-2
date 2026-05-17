from __future__ import annotations

from typing import TYPE_CHECKING, Any

import httpx

from job_finder.models import JobPost, normalize_datetime

if TYPE_CHECKING:
    from job_finder.config import AdzunaConfig


class AdzunaAdapter:
    name = "adzuna"
    base_url = "https://api.adzuna.com/v1/api/jobs"

    def __init__(
        self,
        config: AdzunaConfig,
        app_id: str,
        app_key: str,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.config = config
        self.app_id = app_id
        self.app_key = app_key
        self.client = client

    async def fetch(self) -> list[JobPost]:
        close_client = self.client is None
        client = self.client or httpx.AsyncClient(timeout=30.0, follow_redirects=True)
        try:
            jobs: list[JobPost] = []
            seen: set[str] = set()
            locations = self.config.locations or [""]
            for country_code in self.config.country_codes:
                for term in self.config.search_terms:
                    for location in locations:
                        for page in range(1, self.config.max_pages + 1):
                            response = await client.get(
                                f"{self.base_url}/{country_code}/search/{page}",
                                params={
                                    "app_id": self.app_id,
                                    "app_key": self.app_key,
                                    "what": term,
                                    "where": location,
                                    "results_per_page": self.config.results_per_page,
                                    "sort_by": "date",
                                    "content-type": "application/json",
                                },
                                headers={"Accept": "application/json"},
                            )
                            response.raise_for_status()
                            payload = response.json()
                            page_jobs = payload.get("results", [])
                            if not page_jobs:
                                break
                            for item in page_jobs:
                                job = self._parse_job(country_code, item)
                                key = job.url or f"{job.source}:{job.source_id}"
                                if key in seen:
                                    continue
                                seen.add(key)
                                jobs.append(job)
            return jobs
        finally:
            if close_client:
                await client.aclose()

    def _parse_job(self, country_code: str, item: dict[str, Any]) -> JobPost:
        company = item.get("company") or {}
        location = item.get("location") or {}
        category = item.get("category") or {}
        location_name = str(location.get("display_name") or "").strip()
        description_parts = [
            str(item.get("description") or ""),
            str(category.get("label") or ""),
            str(item.get("contract_time") or ""),
        ]
        return JobPost(
            source=self.name,
            source_id=str(item.get("id") or ""),
            title=str(item.get("title") or "").strip(),
            company=str(company.get("display_name") or "").strip(),
            url=str(item.get("redirect_url") or item.get("url") or "").strip(),
            location=location_name,
            remote=_looks_remote(
                " ".join(
                    [
                        str(item.get("title") or ""),
                        location_name,
                        str(item.get("description") or ""),
                    ]
                )
            ),
            description=" ".join(part for part in description_parts if part),
            published_at=normalize_datetime(item.get("created")),
            raw={**item, "country_code": country_code},
        )


def _looks_remote(value: str) -> bool | None:
    if not value:
        return None
    normalized = value.lower()
    if "remote" in normalized or "work from home" in normalized:
        return True
    return None
