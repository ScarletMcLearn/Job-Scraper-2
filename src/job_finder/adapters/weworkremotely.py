from __future__ import annotations

from xml.etree import ElementTree

import httpx

from job_finder.config import WeWorkRemotelyConfig
from job_finder.models import JobPost, normalize_datetime


class WeWorkRemotelyAdapter:
    name = "weworkremotely"

    def __init__(
        self,
        config: WeWorkRemotelyConfig,
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
                root = ElementTree.fromstring(response.content)
                for item in root.findall(".//item")[: self.config.max_items_per_feed]:
                    job = self._parse_item(item)
                    key = job.url or f"{job.source}:{job.source_id}"
                    if key in seen:
                        continue
                    seen.add(key)
                    jobs.append(job)
            return jobs
        finally:
            if close_client:
                await client.aclose()

    def _parse_item(self, item: ElementTree.Element) -> JobPost:
        raw_title = _child_text(item, "title")
        company, title = _split_title(raw_title)
        link = _child_text(item, "link")
        guid = _child_text(item, "guid") or link
        categories = [child.text or "" for child in item.findall("category")]
        description_parts = [
            _child_text(item, "description"),
            "Categories: " + ", ".join(category for category in categories if category),
        ]

        return JobPost(
            source=self.name,
            source_id=guid,
            title=title,
            company=company,
            url=link,
            location="Remote",
            remote=True,
            description=" ".join(part for part in description_parts if part),
            published_at=normalize_datetime(_child_text(item, "pubDate")),
            raw={
                "title": raw_title,
                "link": link,
                "guid": guid,
                "categories": categories,
            },
        )


def _child_text(item: ElementTree.Element, tag: str) -> str:
    child = item.find(tag)
    return "" if child is None or child.text is None else child.text.strip()


def _split_title(raw_title: str) -> tuple[str, str]:
    company, separator, title = raw_title.partition(":")
    if separator:
        return company.strip(), title.strip()
    return "", raw_title.strip()
