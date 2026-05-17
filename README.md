# Job Finder

Compliance-first CLI for finding QA/Test/SQA/SDET/automation jobs that show visa,
relocation, or Bangladesh-eligible remote evidence.

The project intentionally does not scrape LinkedIn pages. Use:

```powershell
uv run job-finder linkedin-searches
```

to print manual LinkedIn search URLs.

## Setup

Dependencies are managed with `uv` and pinned exactly in `pyproject.toml`.

```powershell
uv sync
uv run job-finder scan --config config/search.yml
uv run job-finder export --config config/search.yml
uv run pytest
```

Scan results are written to:

- `data/jobs.sqlite`
- `output/jobs.csv`

## Sources

Enabled by default:

- Remotive public API
- Arbeitnow public API

Configured when slugs are added:

- Greenhouse job-board API via `sources.greenhouse.board_tokens`
- Lever postings API via `sources.lever.companies`

LinkedIn direct ingestion is a disabled placeholder until authorized API, licensed
data, or exported data access is available.
