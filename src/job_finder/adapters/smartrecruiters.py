from __future__ import annotations

from typing import Any

import httpx

from job_finder.config import SmartRecruitersConfig
from job_finder.models import JobPost, normalize_datetime


class SmartRecruitersAdapter:
    name = "smartrecruiters"
    base_url = "https://api.smartrecruiters.com/v1/companies"

    def __init__(
        self,
        config: SmartRecruitersConfig,
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
            for company in self.config.companies:
                for query in self.config.search_terms or [None]:
                    params: dict[str, Any] = {"limit": self.config.limit}
                    if query:
                        params["q"] = query
                    response = await client.get(f"{self.base_url}/{company}/postings", params=params)
                    response.raise_for_status()
                    payload = response.json()
                    for item in payload.get("content", []):
                        detail = await self._fetch_detail(client, company, item)
                        job = self._parse_job(company, item, detail)
                        key = job.url or f"{job.source}:{job.source_id}"
                        if key in seen:
                            continue
                        seen.add(key)
                        jobs.append(job)
            return jobs
        finally:
            if close_client:
                await client.aclose()

    async def _fetch_detail(
        self,
        client: httpx.AsyncClient,
        company: str,
        item: dict,
    ) -> dict:
        posting_id = item.get("id") or item.get("uuid")
        if not posting_id:
            return {}
        try:
            response = await client.get(f"{self.base_url}/{company}/postings/{posting_id}")
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError:
            return {}
        return payload if isinstance(payload, dict) else {}

    def _parse_job(self, company_slug: str, item: dict, detail: dict) -> JobPost:
        record = detail or item
        company = record.get("company") or item.get("company") or {}
        location = record.get("location") or item.get("location") or {}
        return JobPost(
            source=self.name,
            source_id=str(record.get("id") or item.get("id") or item.get("uuid") or ""),
            title=str(record.get("name") or item.get("name") or "").strip(),
            company=str(company.get("name") or company_slug).strip(),
            url=str(record.get("applyUrl") or item.get("ref") or "").strip(),
            location=_format_location(location),
            remote=_remote_flag(location),
            description=_format_description(record),
            published_at=normalize_datetime(record.get("releasedDate") or item.get("releasedDate")),
            raw=record,
        )


def _format_location(location: object) -> str:
    if not isinstance(location, dict):
        return str(location or "").strip()
    parts = [
        str(location.get("city") or "").strip(),
        str(location.get("region") or "").strip(),
        str(location.get("country") or "").strip(),
    ]
    return ", ".join(part for part in parts if part)


def _remote_flag(location: object) -> bool | None:
    if not isinstance(location, dict):
        return None
    remote = location.get("remote")
    return remote if isinstance(remote, bool) else None


def _format_description(record: dict) -> str:
    job_ad = record.get("jobAd") or {}
    sections = job_ad.get("sections") or {}
    description_parts: list[str] = []
    if isinstance(sections, dict):
        for section in sections.values():
            if isinstance(section, dict):
                description_parts.append(str(section.get("text") or ""))
    for key in ("department", "function", "typeOfEmployment", "experienceLevel"):
        value = record.get(key)
        if isinstance(value, dict):
            description_parts.append(str(value.get("label") or value.get("description") or ""))
    return " ".join(part for part in description_parts if part)
