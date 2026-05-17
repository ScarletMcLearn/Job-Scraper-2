# Job Finder

Compliance-first CLI for finding QA/Test/SQA/SDET/automation jobs that show visa,
relocation, or Bangladesh-eligible remote evidence.

The project intentionally does not scrape LinkedIn pages. Use:

```powershell
uv --cache-dir .uv-cache run job-finder linkedin-searches
```

to print manual LinkedIn search URLs.

## Setup

Dependencies are managed with `uv` and pinned exactly in `pyproject.toml`.

```powershell
uv --cache-dir .uv-cache sync
uv --cache-dir .uv-cache run job-finder scan --config config/search.yml
uv --cache-dir .uv-cache run job-finder export --config config/search.yml
uv --cache-dir .uv-cache run ruff check .
uv --cache-dir .uv-cache run ruff format .
uv --cache-dir .uv-cache run pytest
```

Scan results are written to:

- `data/jobs.sqlite`
- `output/jobs.csv`

To run the full search and save a timestamped Markdown report:

```powershell
.\run-job-search.ps1
```

Reports are written under `artifacts/jobs/yy-mm-dd-hh-mm-ss-am/jobs.md`.

## Strictness modes

Set `filters.strictness` in `config/search.yml`:

```yaml
filters:
  strictness: lenient
```

- `strict`: only include roles with explicit visa, relocation, or eligible remote evidence.
- `evidence`: default safe mode; uncertain remote roles go to review.
- `broad`: includes uncertain remote roles.
- `lenient`: also accepts QA evidence from descriptions and reviews weak matches.
- `discovery`: highest-volume mode; includes weak QA matches unless a hard blocker is found.

## Sources

Enabled by default:

- Remotive public API
- Arbeitnow public API
- Himalayas public remote jobs API
- Jobicy public remote jobs API
- Remote OK public API
- RemoteJobs.org public API
- We Work Remotely public RSS feed

Configured when slugs are added:

- Ashby job-board API via `sources.ashby.organization_names`
- Greenhouse job-board API via `sources.greenhouse.board_tokens`
- Lever postings API via `sources.lever.companies`
- SmartRecruiters postings API via `sources.smartrecruiters.companies`

LinkedIn direct ingestion is a disabled placeholder until authorized API, licensed
data, or exported data access is available.

Remote OK, RemoteJobs.org, and We Work Remotely request source attribution/link-back
when their listings are displayed. The CSV keeps the source name and original job URL
for each row.
