from __future__ import annotations

from typing import TYPE_CHECKING
from xml.etree import ElementTree as ET

import httpx

from job_finder.models import JobPost, normalize_datetime

if TYPE_CHECKING:
    from job_finder.config import RecruiteeConfig


class RecruiteeAdapter:
    name = "recruitee"

    def __init__(
        self,
        config: RecruiteeConfig,
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
            for feed_url in self.config.feed_urls:
                response = await client.get(feed_url)
                response.raise_for_status()
                root = ET.fromstring(response.content)  # noqa: S314
                for item in root.findall(".//job"):
                    job = self._parse_job(item, feed_url)
                    key = job.url or f"{job.source}:{job.source_id}"
                    if key in seen:
                        continue
                    seen.add(key)
                    jobs.append(job)
            return jobs
        finally:
            if close_client:
                await client.aclose()

    def _parse_job(self, item: ET.Element, feed_url: str) -> JobPost:
        description_parts = [
            _child_text(item, "description_requirements"),
            _child_text(item, "category"),
            _child_text(item, "contract_type"),
            _child_text(item, "experience"),
        ]
        posted = _child_text(item, "posted")
        updated = _child_text(item, "updated")
        return JobPost(
            source=self.name,
            source_id=_child_text(item, "reference"),
            title=_child_text(item, "title"),
            company=_child_text(item, "company"),
            url=_child_text(item, "url") or _child_text(item, "apply_url"),
            location=_format_location(item),
            remote=_remote_flag(item),
            description=" ".join(part for part in description_parts if part),
            published_at=normalize_datetime(posted or updated),
            raw={"feed_url": feed_url, "reference": _child_text(item, "reference")},
        )


def _child_text(item: ET.Element, tag: str) -> str:
    child = item.find(tag)
    return "" if child is None or child.text is None else child.text.strip()


def _format_location(item: ET.Element) -> str:
    locations: list[str] = []
    for location in item.findall(".//locations/location"):
        parts = [
            _child_text(location, "city"),
            _child_text(location, "state"),
            _child_text(location, "country"),
        ]
        value = ", ".join(part for part in parts if part)
        if value:
            locations.append(value)
    if locations:
        return ", ".join(locations)
    parts = [
        _child_text(item, "city"),
        _child_text(item, "state"),
        _child_text(item, "country"),
    ]
    return ", ".join(part for part in parts if part)


def _remote_flag(item: ET.Element) -> bool | None:
    remote = _child_text(item, "remote").lower()
    if remote == "true":
        return True
    if remote == "false":
        return False
    return None
