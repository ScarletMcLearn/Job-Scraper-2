from __future__ import annotations

from pathlib import Path
from urllib.parse import urlencode

import typer
from rich.console import Console
from rich.table import Table

from job_finder.config import AppConfig, dump_default_config, load_config
from job_finder.models import MatchStatus
from job_finder.runner import run_scan
from job_finder.storage import JobStore

app = typer.Typer(
    add_completion=False,
    help="Find QA/Test/SQA/SDET roles with visa, relocation, or Bangladesh-eligible remote support.",
)
console = Console()


@app.command()
def scan(
    config: Path = typer.Option(
        Path("config/search.yml"),
        "--config",
        "-c",
        help="Path to the YAML search config.",
    ),
) -> None:
    """Fetch configured sources, filter jobs, save SQLite, and export CSV."""
    app_config = _load_or_create_config(config)
    summary = run_scan(app_config, console)

    table = Table(title=f"Scan {summary.run_id}")
    table.add_column("Metric")
    table.add_column("Count", justify="right")
    table.add_row("Fetched", str(summary.fetched))
    table.add_row("Included", str(summary.included))
    table.add_row("Review", str(summary.review))
    table.add_row("Excluded", str(summary.excluded))
    table.add_row("Adapter errors", str(len(summary.adapter_errors)))
    console.print(table)


@app.command("linkedin-searches")
def linkedin_searches(
    config: Path = typer.Option(
        Path("config/search.yml"),
        "--config",
        "-c",
        help="Path to the YAML search config.",
    ),
) -> None:
    """Print manual LinkedIn search URLs; this does not scrape LinkedIn."""
    app_config = _load_or_create_config(config)
    query = _linkedin_boolean_query()
    for location in app_config.sources.linkedin.manual_locations:
        params = urlencode({"keywords": query, "location": location})
        console.print(f"{location}: https://www.linkedin.com/jobs/search/?{params}")


@app.command()
def export(
    config: Path = typer.Option(
        Path("config/search.yml"),
        "--config",
        "-c",
        help="Path to the YAML search config.",
    ),
    include_excluded: bool = typer.Option(
        False,
        "--include-excluded",
        help="Also export excluded rows.",
    ),
) -> None:
    """Export existing SQLite results to CSV."""
    app_config = _load_or_create_config(config)
    statuses = (MatchStatus.INCLUDED, MatchStatus.REVIEW)
    if include_excluded:
        statuses = (MatchStatus.INCLUDED, MatchStatus.REVIEW, MatchStatus.EXCLUDED)
    store = JobStore(app_config.output.database_path)
    try:
        count = store.export_csv(app_config.output.csv_path, statuses=statuses)
    finally:
        store.close()
    console.print(
        f"[green]Exported[/green] {count} rows to {app_config.output.csv_path}"
    )


@app.command("export-markdown")
def export_markdown(
    config: Path = typer.Option(
        Path("config/search.yml"),
        "--config",
        "-c",
        help="Path to the YAML search config.",
    ),
    output: Path = typer.Option(
        Path("output/jobs.md"),
        "--output",
        "-o",
        help="Path for the Markdown report.",
    ),
    include_excluded: bool = typer.Option(
        False,
        "--include-excluded",
        help="Also export excluded rows.",
    ),
) -> None:
    """Export existing SQLite results to Markdown."""
    app_config = _load_or_create_config(config)
    statuses = (MatchStatus.INCLUDED, MatchStatus.REVIEW)
    if include_excluded:
        statuses = (MatchStatus.INCLUDED, MatchStatus.REVIEW, MatchStatus.EXCLUDED)
    store = JobStore(app_config.output.database_path)
    try:
        count = store.export_markdown(output, statuses=statuses)
    finally:
        store.close()
    console.print(f"[green]Exported[/green] {count} rows to {output}")


def _load_or_create_config(path: Path) -> AppConfig:
    if not path.exists():
        dump_default_config(path)
        console.print(f"[yellow]Created default config[/yellow] at {path}")
    return load_config(path)


def _linkedin_boolean_query() -> str:
    role_terms = [
        "QA",
        "Test",
        "SQA",
        "SDET",
        '"quality assurance"',
        '"software quality assurance"',
        '"software development engineer in test"',
        "automation",
        "selenium",
        "cypress",
        "playwright",
    ]
    support_terms = ["relocation", "visa", "sponsor", "remote"]
    return f"({' OR '.join(role_terms)}) AND ({' OR '.join(support_terms)})"
