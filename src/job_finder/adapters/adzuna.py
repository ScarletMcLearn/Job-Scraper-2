from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import httpx

from job_finder.models import JobPost, normalize_datetime

if TYPE_CHECKING:
    from collections.abc import Mapping

    from job_finder.config import AdzunaConfig


@dataclass(frozen=True)
class _AdzunaQuery:
    country_code: str
    term: str
    location: str


class AdzunaAdapter:
    name = "adzuna"
    base_url = "https://api.adzuna.com/v1/api/jobs"
    rate_limited_status = 429

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
            return await self._fetch_jobs(client)
        finally:
            if close_client:
                await client.aclose()

    async def _fetch_jobs(self, client: httpx.AsyncClient) -> list[JobPost]:
        jobs: list[JobPost] = []
        seen: set[str] = set()
        locations = self.config.locations or [""]
        for country_code in self.config.country_codes:
            for term in self.config.search_terms:
                for location in locations:
                    query = _AdzunaQuery(country_code, term, location)
                    should_continue = await self._collect_pages(
                        client, jobs, seen, query
                    )
                    if not should_continue:
                        return jobs
        return jobs

    async def _collect_pages(
        self,
        client: httpx.AsyncClient,
        jobs: list[JobPost],
        seen: set[str],
        query: _AdzunaQuery,
    ) -> bool:
        for page in range(1, self.config.max_pages + 1):
            page_jobs = await self._fetch_page(client, query, page)
            if page_jobs is None:
                return False
            if not page_jobs:
                break
            for item in page_jobs:
                job = self._parse_job(query.country_code, item)
                key = job.url or f"{job.source}:{job.source_id}"
                if key in seen:
                    continue
                seen.add(key)
                jobs.append(job)
            if self.config.request_delay_seconds > 0:
                await asyncio.sleep(self.config.request_delay_seconds)
        return True

    async def _fetch_page(
        self,
        client: httpx.AsyncClient,
        query: _AdzunaQuery,
        page: int,
    ) -> list[dict[str, Any]] | None:
        response = await client.get(
            f"{self.base_url}/{query.country_code}/search/{page}",
            params=_clean_params(
                {
                    "app_id": self.app_id,
                    "app_key": self.app_key,
                    "what": query.term,
                    "where": query.location,
                    "results_per_page": self.config.results_per_page,
                    "sort_by": "date",
                    "content-type": "application/json",
                }
            ),
            headers={"Accept": "application/json"},
        )
        if response.status_code == self.rate_limited_status:
            return None
        if response.is_error:
            _raise_adzuna_status_error(response, query.country_code, page)
        payload = response.json()
        page_jobs = payload.get("results", [])
        if not isinstance(page_jobs, list):
            return []
        return page_jobs

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


def _clean_params(params: Mapping[str, str | int | None]) -> dict[str, str | int]:
    return {key: value for key, value in params.items() if value not in (None, "")}


def _raise_adzuna_status_error(
    response: httpx.Response, country_code: str, page: int
) -> None:
    message = (
        f"Adzuna API returned HTTP {response.status_code} "
        f"for country {country_code}, page {page}."
    )
    raise httpx.HTTPStatusError(message, request=response.request, response=response)
