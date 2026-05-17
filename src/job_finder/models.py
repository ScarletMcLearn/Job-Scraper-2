from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, HttpUrl, field_serializer


class MatchStatus(StrEnum):
    INCLUDED = "included"
    REVIEW = "review"
    EXCLUDED = "excluded"


class JobPost(BaseModel):
    source: str
    source_id: str | None = None
    title: str
    company: str
    url: str
    location: str = ""
    remote: bool | None = None
    description: str = ""
    published_at: datetime | None = None
    raw: dict[str, Any] = Field(default_factory=dict)

    def searchable_text(self) -> str:
        return " ".join(
            part
            for part in [
                self.title,
                self.company,
                self.location,
                html_to_text(self.description),
            ]
            if part
        )


class JobMatch(BaseModel):
    job: JobPost
    status: MatchStatus
    matched_keywords: list[str] = Field(default_factory=list)
    support_evidence: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)

    @field_serializer("status")
    def serialize_status(self, status: MatchStatus) -> str:
        return status.value


class ScanSummary(BaseModel):
    run_id: int
    fetched: int = 0
    included: int = 0
    review: int = 0
    excluded: int = 0
    adapter_errors: dict[str, str] = Field(default_factory=dict)


def now_utc() -> datetime:
    return datetime.now(UTC)


def html_to_text(value: str) -> str:
    if not value:
        return ""
    return BeautifulSoup(value, "html.parser").get_text(" ", strip=True)


def normalize_datetime(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, int | float):
        if value > 10_000_000_000:
            value = value / 1000
        return datetime.fromtimestamp(value, tz=UTC)

    from dateutil.parser import parse

    try:
        parsed = parse(str(value))
    except (TypeError, ValueError, OverflowError):
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def validated_url(value: str) -> str:
    if not value:
        return ""
    return str(HttpUrl(value))
