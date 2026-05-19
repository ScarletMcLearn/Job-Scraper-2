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
    "QA engineer",
    "QA analyst",
    "quality engineer",
    "quality assurance",
    "software quality engineer",
    "software quality assurance",
    "software development engineer in test",
    "test engineer",
    "test automation",
    "manual tester",
    "automation",
    "automation engineer",
    "selenium",
    "cypress",
    "playwright",
]

DEFAULT_SEARCH_TERMS = [
    "qa",
    "qa engineer",
    "qa analyst",
    "quality assurance",
    "quality engineer",
    "software quality engineer",
    "test engineer",
    "test automation",
    "manual tester",
    "sdet",
    "automation engineer",
]

DEFAULT_ASHBY_ORGANIZATION_NAMES = ["Ashby", "OpenAI", "supabase"]
DEFAULT_GREENHOUSE_BOARD_TOKENS = ["gitlab", "canonical"]
DEFAULT_LEVER_COMPANIES = [
    "revealtech",
    "insiderone",
    "chooose",
    "pingwind",
    "heartbeathealth",
    "getwingapp",
    "caseware",
]
DEFAULT_SMARTRECRUITERS_COMPANIES = ["SmartRecruiters"]

StrictnessMode = Literal["strict", "evidence", "broad", "lenient", "discovery"]


class RemotiveConfig(BaseModel):
    enabled: bool = True
    search_terms: list[str] = Field(default_factory=DEFAULT_SEARCH_TERMS.copy)


class ArbeitnowConfig(BaseModel):
    enabled: bool = True
    max_pages: int = 2


class HimalayasConfig(BaseModel):
    enabled: bool = True
    search_terms: list[str] = Field(default_factory=DEFAULT_SEARCH_TERMS.copy)
    max_pages: int = 2
    page_size: int = 20


class JobicyConfig(BaseModel):
    enabled: bool = True
    search_terms: list[str] = Field(default_factory=DEFAULT_SEARCH_TERMS.copy)
    count: int = 50


class RemoteOkConfig(BaseModel):
    enabled: bool = True
    max_results: int = 100


class RemoteJobsOrgConfig(BaseModel):
    enabled: bool = True
    search_terms: list[str] = Field(default_factory=DEFAULT_SEARCH_TERMS.copy)
    limit: int = 50
    max_pages: int = 2


class WeWorkRemotelyConfig(BaseModel):
    enabled: bool = True
    feed_urls: list[str] = Field(
        default_factory=lambda: ["https://weworkremotely.com/remote-jobs.rss"]
    )
    max_items_per_feed: int = 100


class AshbyConfig(BaseModel):
    enabled: bool = True
    organization_names: list[str] = Field(
        default_factory=DEFAULT_ASHBY_ORGANIZATION_NAMES.copy
    )
    include_compensation: bool = False


class GreenhouseConfig(BaseModel):
    enabled: bool = True
    board_tokens: list[str] = Field(default_factory=DEFAULT_GREENHOUSE_BOARD_TOKENS.copy)


class LeverConfig(BaseModel):
    enabled: bool = True
    companies: list[str] = Field(default_factory=DEFAULT_LEVER_COMPANIES.copy)


class SmartRecruitersConfig(BaseModel):
    enabled: bool = True
    companies: list[str] = Field(default_factory=DEFAULT_SMARTRECRUITERS_COMPANIES.copy)
    search_terms: list[str] = Field(default_factory=DEFAULT_SEARCH_TERMS.copy)
    limit: int = 50


class TheMuseConfig(BaseModel):
    enabled: bool = True
    api_key_env: str = "THEMUSE_API_KEY"
    categories: list[str] = Field(
        default_factory=lambda: ["Software Engineering", "Science and Engineering"]
    )
    locations: list[str] = Field(default_factory=lambda: ["Flexible / Remote", "Remote"])
    max_pages: int = 2


class AdzunaConfig(BaseModel):
    enabled: bool = True
    app_id_env: str = "ADZUNA_APP_ID"
    app_key_env: str = "ADZUNA_APP_KEY"
    search_terms: list[str] = Field(default_factory=DEFAULT_SEARCH_TERMS.copy)
    country_codes: list[str] = Field(
        default_factory=lambda: ["gb", "us", "ca", "au", "sg", "in"]
    )
    locations: list[str] = Field(default_factory=lambda: ["remote", ""])
    max_pages: int = 2
    results_per_page: int = 50
    request_delay_seconds: float = 0.0


class JoobleConfig(BaseModel):
    enabled: bool = True
    api_key_env: str = "JOOBLE_API_KEY"
    search_terms: list[str] = Field(default_factory=DEFAULT_SEARCH_TERMS.copy)
    locations: list[str] = Field(
        default_factory=lambda: ["Remote", "Worldwide", "Bangladesh"]
    )
    max_pages: int = 2
    results_per_page: int = 50


class WorkableConfig(BaseModel):
    enabled: bool = True
    account_subdomains: list[str] = Field(default_factory=list)


class RecruiteeConfig(BaseModel):
    enabled: bool = True
    feed_urls: list[str] = Field(default_factory=list)


class WorkAnywhereConfig(BaseModel):
    enabled: bool = False
    feed_urls: list[str] = Field(
        default_factory=lambda: [
            "https://workanywhere.pro/rss.xml",
            "https://workanywhere.pro/rss/engineer.xml",
        ]
    )
    max_items_per_feed: int = 100


class LinkedinConfig(BaseModel):
    enabled: bool = False
    manual_locations: list[str] = Field(
        default_factory=lambda: ["Worldwide", "Remote", "Bangladesh"]
    )


class SourcesConfig(BaseModel):
    remotive: RemotiveConfig = Field(default_factory=RemotiveConfig)
    arbeitnow: ArbeitnowConfig = Field(default_factory=ArbeitnowConfig)
    himalayas: HimalayasConfig = Field(default_factory=HimalayasConfig)
    jobicy: JobicyConfig = Field(default_factory=JobicyConfig)
    remoteok: RemoteOkConfig = Field(default_factory=RemoteOkConfig)
    remotejobs_org: RemoteJobsOrgConfig = Field(default_factory=RemoteJobsOrgConfig)
    weworkremotely: WeWorkRemotelyConfig = Field(default_factory=WeWorkRemotelyConfig)
    themuse: TheMuseConfig = Field(default_factory=TheMuseConfig)
    adzuna: AdzunaConfig = Field(default_factory=AdzunaConfig)
    jooble: JoobleConfig = Field(default_factory=JoobleConfig)
    workable: WorkableConfig = Field(default_factory=WorkableConfig)
    recruitee: RecruiteeConfig = Field(default_factory=RecruiteeConfig)
    workanywhere: WorkAnywhereConfig = Field(default_factory=WorkAnywhereConfig)
    ashby: AshbyConfig = Field(default_factory=AshbyConfig)
    greenhouse: GreenhouseConfig = Field(default_factory=GreenhouseConfig)
    lever: LeverConfig = Field(default_factory=LeverConfig)
    smartrecruiters: SmartRecruitersConfig = Field(
        default_factory=SmartRecruitersConfig
    )
    linkedin: LinkedinConfig = Field(default_factory=LinkedinConfig)


class FilterConfig(BaseModel):
    target_country: str = "Bangladesh"
    strictness: StrictnessMode = "evidence"
    role_keywords: list[str] = Field(default_factory=DEFAULT_ROLE_KEYWORDS.copy)


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
        msg = f"Config file must contain a YAML mapping: {path}"
        raise TypeError(msg)
    return AppConfig.model_validate(data)


def dump_default_config(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, Any] = AppConfig().model_dump(mode="json")
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
