from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field


DEFAULT_ROLE_KEYWORDS = [
    "QA",
    "Test",
    "SQA",
    "SDET",
    "quality assurance",
    "software quality assurance",
    "software development engineer in test",
    "automation",
    "selenium",
    "cypress",
    "playwright",
]


class RemotiveConfig(BaseModel):
    enabled: bool = True
    search_terms: list[str] = Field(
        default_factory=lambda: ["qa", "test automation", "sdet", "quality assurance"]
    )


class ArbeitnowConfig(BaseModel):
    enabled: bool = True
    max_pages: int = 2


class GreenhouseConfig(BaseModel):
    enabled: bool = True
    board_tokens: list[str] = Field(default_factory=list)


class LeverConfig(BaseModel):
    enabled: bool = True
    companies: list[str] = Field(default_factory=list)


class LinkedinConfig(BaseModel):
    enabled: bool = False
    manual_locations: list[str] = Field(
        default_factory=lambda: ["Worldwide", "Remote", "Bangladesh"]
    )


class SourcesConfig(BaseModel):
    remotive: RemotiveConfig = Field(default_factory=RemotiveConfig)
    arbeitnow: ArbeitnowConfig = Field(default_factory=ArbeitnowConfig)
    greenhouse: GreenhouseConfig = Field(default_factory=GreenhouseConfig)
    lever: LeverConfig = Field(default_factory=LeverConfig)
    linkedin: LinkedinConfig = Field(default_factory=LinkedinConfig)


class FilterConfig(BaseModel):
    target_country: str = "Bangladesh"
    strictness: Literal["evidence", "broad", "strict"] = "evidence"
    role_keywords: list[str] = Field(default_factory=lambda: DEFAULT_ROLE_KEYWORDS.copy())


class OutputConfig(BaseModel):
    database_path: Path = Path("data/jobs.sqlite")
    csv_path: Path = Path("output/jobs.csv")


class AppConfig(BaseModel):
    filters: FilterConfig = Field(default_factory=FilterConfig)
    sources: SourcesConfig = Field(default_factory=SourcesConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)


def load_config(path: Path) -> AppConfig:
    if not path.exists():
        return AppConfig()
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config file must contain a YAML mapping: {path}")
    return AppConfig.model_validate(data)


def dump_default_config(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, Any] = AppConfig().model_dump(mode="json")
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
