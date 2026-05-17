from __future__ import annotations

import asyncio

from rich.console import Console

from job_finder.adapters import (
    AshbyAdapter,
    ArbeitnowAdapter,
    GreenhouseAdapter,
    HimalayasAdapter,
    JobicyAdapter,
    LeverAdapter,
    LinkedinAuthorizedPlaceholderAdapter,
    RemoteJobsOrgAdapter,
    RemoteOkAdapter,
    RemotiveAdapter,
    SmartRecruitersAdapter,
    SourceAdapterError,
    WeWorkRemotelyAdapter,
)
from job_finder.config import AppConfig
from job_finder.filtering import JobClassifier
from job_finder.models import MatchStatus, ScanSummary
from job_finder.storage import JobStore


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


def build_adapters(config: AppConfig):
    adapters = []
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
    if config.sources.ashby.enabled and config.sources.ashby.organization_names:
        adapters.append(AshbyAdapter(config.sources.ashby))
    if config.sources.greenhouse.enabled and config.sources.greenhouse.board_tokens:
        adapters.append(GreenhouseAdapter(config.sources.greenhouse))
    if config.sources.lever.enabled and config.sources.lever.companies:
        adapters.append(LeverAdapter(config.sources.lever))
    if config.sources.smartrecruiters.enabled and config.sources.smartrecruiters.companies:
        adapters.append(SmartRecruitersAdapter(config.sources.smartrecruiters))
    if config.sources.linkedin.enabled:
        adapters.append(LinkedinAuthorizedPlaceholderAdapter())
    return adapters


def run_scan(config: AppConfig, console: Console | None = None) -> ScanSummary:
    return asyncio.run(scan(config, console))
