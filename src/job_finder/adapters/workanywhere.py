from __future__ import annotations

from typing import TYPE_CHECKING
from xml.etree import ElementTree as ET

import httpx

from job_finder.models import JobPost, normalize_datetime

if TYPE_CHECKING:
    from job_finder.config import WorkAnywhereConfig


class WorkAnywhereAdapter:
    name = "workanywhere"

    def __init__(
        self,
        config: WorkAnywhereConfig,
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
                for item in root.findall(".//item")[: self.config.max_items_per_feed]:
                    job = self._parse_item(item, feed_url)
                    key = job.url or f"{job.source}:{job.source_id}"
                    if key in seen:
                        continue
                    seen.add(key)
                    jobs.append(job)
            return jobs
        finally:
            if close_client:
                await client.aclose()

    def _parse_item(self, item: ET.Element, feed_url: str) -> JobPost:
        raw_title = _child_text(item, "title")
        company = _child_text(item, "company")
        title = raw_title
        if not company:
            company, title = _split_title(raw_title)
        categories = _children_text(item, "category")
        description_parts = [
            _child_text(item, "description"),
            "Categories: " + ", ".join(categories) if categories else "",
        ]
        link = _child_text(item, "link")
        guid = _child_text(item, "guid") or link
        return JobPost(
            source=self.name,
            source_id=guid,
            title=title,
            company=company,
            url=link,
            location=_child_text(item, "location") or "Remote",
            remote=True,
            description=" ".join(part for part in description_parts if part),
            published_at=normalize_datetime(_child_text(item, "pubDate")),
            raw={"feed_url": feed_url, "title": raw_title, "categories": categories},
        )


def _child_text(item: ET.Element, tag: str) -> str:
    for child in item:
        if _local_name(child.tag) == tag:
            return "" if child.text is None else child.text.strip()
    return ""


def _children_text(item: ET.Element, tag: str) -> list[str]:
    return [
        child.text.strip()
        for child in item
        if _local_name(child.tag) == tag and child.text
    ]


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _split_title(raw_title: str) -> tuple[str, str]:
    company, separator, title = raw_title.partition(":")
    if separator:
        return company.strip(), title.strip()
    title, separator, company = raw_title.rpartition(" at ")
    if separator:
        return company.strip(), title.strip()
    return "", raw_title.strip()
