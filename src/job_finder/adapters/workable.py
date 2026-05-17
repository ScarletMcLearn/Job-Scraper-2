from __future__ import annotations

from typing import TYPE_CHECKING, Any

import httpx

from job_finder.models import JobPost, normalize_datetime

if TYPE_CHECKING:
    from job_finder.config import WorkableConfig


class WorkableAdapter:
    name = "workable"
    base_url = "https://www.workable.com/api/accounts"

    def __init__(
        self,
        config: WorkableConfig,
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
            for subdomain in self.config.account_subdomains:
                response = await client.get(
                    f"{self.base_url}/{subdomain}",
                    params={"details": "true"},
                )
                response.raise_for_status()
                payload = response.json()
                company_name = str(payload.get("name") or subdomain).strip()
                for item in _extract_jobs(payload):
                    job = self._parse_job(subdomain, company_name, item)
                    key = job.url or f"{job.source}:{job.source_id}"
                    if key in seen:
                        continue
                    seen.add(key)
                    jobs.append(job)
            return jobs
        finally:
            if close_client:
                await client.aclose()

    def _parse_job(
        self,
        subdomain: str,
        company_name: str,
        item: dict[str, Any],
    ) -> JobPost:
        location = _format_location(item)
        description_parts = [
            str(item.get("description") or ""),
            str(item.get("requirements") or ""),
            str(item.get("benefits") or ""),
            str(item.get("department") or ""),
            str(item.get("employment_type") or ""),
        ]
        return JobPost(
            source=self.name,
            source_id=str(item.get("id") or item.get("shortcode") or ""),
            title=str(item.get("title") or item.get("full_title") or "").strip(),
            company=company_name,
            url=str(
                item.get("url") or item.get("shortlink") or item.get("application_url") or ""
            ).strip(),
            location=location,
            remote=_remote_flag(item, location),
            description=" ".join(part for part in description_parts if part),
            published_at=normalize_datetime(
                item.get("created_at") or item.get("published_on")
            ),
            raw={**item, "account_subdomain": subdomain},
        )


def _extract_jobs(payload: dict[str, Any]) -> list[dict[str, Any]]:
    jobs = [item for item in payload.get("jobs") or [] if isinstance(item, dict)]
    for department in payload.get("departments") or []:
        if not isinstance(department, dict):
            continue
        jobs.extend(
            item for item in department.get("jobs") or [] if isinstance(item, dict)
        )
    return jobs


def _format_location(item: dict[str, Any]) -> str:
    location = item.get("location")
    if isinstance(location, str):
        return location.strip()
    if isinstance(location, dict):
        return str(
            location.get("location_str")
            or ", ".join(
                part
                for part in [
                    str(location.get("city") or "").strip(),
                    str(location.get("region") or location.get("region_code") or "").strip(),
                    str(location.get("country") or "").strip(),
                ]
                if part
            )
        ).strip()
    locations = item.get("locations")
    if isinstance(locations, list):
        formatted_locations = [
            _format_workable_location(location_item) for location_item in locations
        ]
        return ", ".join(location for location in formatted_locations if location)
    return ""


def _format_workable_location(value: object) -> str:
    if not isinstance(value, dict):
        return str(value or "").strip()
    parts = [
        str(value.get("city") or "").strip(),
        str(value.get("state_code") or value.get("region") or "").strip(),
        str(value.get("country_name") or value.get("country") or "").strip(),
    ]
    return ", ".join(part for part in parts if part)


def _remote_flag(item: dict[str, Any], location: str) -> bool | None:
    location_data = item.get("location")
    if isinstance(location_data, dict):
        telecommuting = location_data.get("telecommuting")
        if isinstance(telecommuting, bool):
            return telecommuting
        workplace_type = str(location_data.get("workplace_type") or "").lower()
        if workplace_type == "remote":
            return True
        if workplace_type in {"on_site", "onsite"}:
            return False
    normalized = f"{item.get('title') or ''} {location}".lower()
    if "remote" in normalized:
        return True
    return None
