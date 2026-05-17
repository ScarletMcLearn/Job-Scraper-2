from __future__ import annotations

import httpx

from job_finder.config import AshbyConfig
from job_finder.models import JobPost, normalize_datetime


class AshbyAdapter:
    name = "ashby"
    base_url = "https://api.ashbyhq.com/posting-api/job-board"

    def __init__(
        self,
        config: AshbyConfig,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.config = config
        self.client = client

    async def fetch(self) -> list[JobPost]:
        close_client = self.client is None
        client = self.client or httpx.AsyncClient(timeout=30.0, follow_redirects=True)
        try:
            jobs: list[JobPost] = []
            for organization_name in self.config.organization_names:
                response = await client.get(
                    f"{self.base_url}/{organization_name}",
                    params={"includeCompensation": str(self.config.include_compensation).lower()},
                )
                response.raise_for_status()
                payload = response.json()
                for item in payload.get("jobs", []):
                    if item.get("isListed") is False:
                        continue
                    jobs.append(self._parse_job(organization_name, item))
            return jobs
        finally:
            if close_client:
                await client.aclose()

    def _parse_job(self, organization_name: str, item: dict) -> JobPost:
        return JobPost(
            source=self.name,
            source_id=str(item.get("id") or item.get("jobUrl") or ""),
            title=str(item.get("title") or "").strip(),
            company=organization_name,
            url=str(item.get("jobUrl") or item.get("applyUrl") or "").strip(),
            location=_format_locations(item),
            remote=_remote_flag(item),
            description=str(item.get("descriptionHtml") or item.get("descriptionPlain") or ""),
            published_at=normalize_datetime(item.get("publishedAt")),
            raw=item,
        )


def _format_locations(item: dict) -> str:
    locations = [str(item.get("location") or "").strip()]
    for location in item.get("secondaryLocations") or []:
        if isinstance(location, dict):
            locations.append(str(location.get("location") or "").strip())
        else:
            locations.append(str(location).strip())
    return ", ".join(location for location in locations if location)


def _remote_flag(item: dict) -> bool | None:
    is_remote = item.get("isRemote")
    if isinstance(is_remote, bool):
        return is_remote
    workplace_type = str(item.get("workplaceType") or "").lower()
    if workplace_type == "remote":
        return True
    if workplace_type == "onsite":
        return False
    return None
