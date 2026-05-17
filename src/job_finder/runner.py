from __future__ import annotations

import asyncio
import os
from typing import TYPE_CHECKING

from rich.console import Console

from job_finder.adapters import (
    AdzunaAdapter,
    ArbeitnowAdapter,
    AshbyAdapter,
    GreenhouseAdapter,
    HimalayasAdapter,
    JobicyAdapter,
    JoobleAdapter,
    LeverAdapter,
    LinkedinAuthorizedPlaceholderAdapter,
    RecruiteeAdapter,
    RemoteJobsOrgAdapter,
    RemoteOkAdapter,
    RemotiveAdapter,
    SkippedSourceAdapter,
    SmartRecruitersAdapter,
    SourceAdapterError,
    TheMuseAdapter,
    WeWorkRemotelyAdapter,
    WorkableAdapter,
    WorkAnywhereAdapter,
)
from job_finder.filtering import JobClassifier
from job_finder.models import MatchStatus, ScanSummary
from job_finder.storage import JobStore

if TYPE_CHECKING:
    from job_finder.adapters.base import JobSourceAdapter
    from job_finder.config import AppConfig


async def scan(config: AppConfig, console: Console | None = None) -> ScanSummary:
    console = console or Console()
    adapters = build_adapters(config)
    store = JobStore(config.output.database_path)
    run_id = store.start_run()
    classifier = JobClassifier(config.filters)
    summary = ScanSummary(run_id=run_id)

    try:
        for adapter in adapters:
            try:
                console.print(f"[cyan]Fetching[/cyan] {adapter.name}...")
                jobs = await adapter.fetch()
            except SourceAdapterError as error:
                summary.adapter_errors[adapter.name] = str(error)
                console.print(f"[yellow]Skipped[/yellow] {adapter.name}: {error}")
                continue
            except Exception as error:  # noqa: BLE001 - preserve scan progress across sources.
                summary.adapter_errors[adapter.name] = str(error)
                console.print(f"[red]Failed[/red] {adapter.name}: {error}")
                continue

            summary.fetched += len(jobs)
            for job in jobs:
                match = classifier.classify(job)
                store.upsert_match(run_id, match)
                if match.status == MatchStatus.INCLUDED:
                    summary.included += 1
                elif match.status == MatchStatus.REVIEW:
                    summary.review += 1
                else:
                    summary.excluded += 1

        exported = store.export_csv(config.output.csv_path)
        console.print(
            f"[green]Exported[/green] {exported} included/review jobs to {config.output.csv_path}"
        )
        return summary
    finally:
        store.complete_run(run_id)
        store.close()


def build_adapters(config: AppConfig) -> list[JobSourceAdapter]:
    adapters: list[JobSourceAdapter] = []
    _add_open_sources(adapters, config)
    _add_keyed_sources(adapters, config)
    _add_configured_board_sources(adapters, config)
    if config.sources.linkedin.enabled:
        adapters.append(LinkedinAuthorizedPlaceholderAdapter())
    return adapters


def _add_open_sources(adapters: list[JobSourceAdapter], config: AppConfig) -> None:
    if config.sources.remotive.enabled:
        adapters.append(RemotiveAdapter(config.sources.remotive))
    if config.sources.arbeitnow.enabled:
        adapters.append(ArbeitnowAdapter(config.sources.arbeitnow))
    if config.sources.himalayas.enabled:
        adapters.append(HimalayasAdapter(config.sources.himalayas))
    if config.sources.jobicy.enabled:
        adapters.append(JobicyAdapter(config.sources.jobicy))
    if config.sources.remoteok.enabled:
        adapters.append(RemoteOkAdapter(config.sources.remoteok))
    if config.sources.remotejobs_org.enabled:
        adapters.append(RemoteJobsOrgAdapter(config.sources.remotejobs_org))
    if config.sources.weworkremotely.enabled:
        adapters.append(WeWorkRemotelyAdapter(config.sources.weworkremotely))
    if config.sources.themuse.enabled:
        adapters.append(
            TheMuseAdapter(
                config.sources.themuse,
                api_key=_env_value(config.sources.themuse.api_key_env),
            )
        )
    if config.sources.workanywhere.enabled:
        adapters.append(WorkAnywhereAdapter(config.sources.workanywhere))


def _add_keyed_sources(adapters: list[JobSourceAdapter], config: AppConfig) -> None:
    if config.sources.adzuna.enabled:
        app_id = _env_value(config.sources.adzuna.app_id_env)
        app_key = _env_value(config.sources.adzuna.app_key_env)
        if app_id and app_key:
            adapters.append(AdzunaAdapter(config.sources.adzuna, app_id, app_key))
        else:
            adapters.append(
                SkippedSourceAdapter(
                    "adzuna",
                    "Set "
                    f"{config.sources.adzuna.app_id_env} and "
                    f"{config.sources.adzuna.app_key_env} to enable Adzuna.",
                )
            )
    if config.sources.jooble.enabled:
        api_key = _env_value(config.sources.jooble.api_key_env)
        if api_key:
            adapters.append(JoobleAdapter(config.sources.jooble, api_key))
        else:
            adapters.append(
                SkippedSourceAdapter(
                    "jooble",
                    f"Set {config.sources.jooble.api_key_env} to enable Jooble.",
                )
            )


def _add_configured_board_sources(
    adapters: list[JobSourceAdapter],
    config: AppConfig,
) -> None:
    if config.sources.workable.enabled and config.sources.workable.account_subdomains:
        adapters.append(WorkableAdapter(config.sources.workable))
    if config.sources.recruitee.enabled and config.sources.recruitee.feed_urls:
        adapters.append(RecruiteeAdapter(config.sources.recruitee))
    if config.sources.ashby.enabled and config.sources.ashby.organization_names:
        adapters.append(AshbyAdapter(config.sources.ashby))
    if config.sources.greenhouse.enabled and config.sources.greenhouse.board_tokens:
        adapters.append(GreenhouseAdapter(config.sources.greenhouse))
    if config.sources.lever.enabled and config.sources.lever.companies:
        adapters.append(LeverAdapter(config.sources.lever))
    if (
        config.sources.smartrecruiters.enabled
        and config.sources.smartrecruiters.companies
    ):
        adapters.append(SmartRecruitersAdapter(config.sources.smartrecruiters))


def _env_value(name: str) -> str | None:
    value = os.environ.get(name)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def run_scan(config: AppConfig, console: Console | None = None) -> ScanSummary:
    return asyncio.run(scan(config, console))
