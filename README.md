# Job Finder

Compliance-first CLI for finding QA/Test/SQA/SDET/automation jobs that show visa,
relocation, or Bangladesh-eligible remote evidence.

The project intentionally does not scrape LinkedIn pages. LinkedIn scan support
must wait for approved LinkedIn API access, licensed job data, or exported job
data access. Use:

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

The workflow prompts for a strictness mode before scanning. You can also skip
the prompt by passing one explicitly:

```powershell
.\run-job-search.ps1 -Strictness strict
```

Reports are written under `artifacts/jobs/yy-mm-dd-hh-mm-ss-am/jobs.md`.

## Strictness modes

Set `filters.strictness` in `config/search.yml`:

```yaml
filters:
  strictness: lenient
```

For a one-off scan without editing the config, pass `--strictness`:

```powershell
uv --cache-dir .uv-cache run job-finder scan --config config/search.yml --strictness strict
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
- The Muse public jobs API

Configured when slugs are added:

- Ashby job-board API via `sources.ashby.organization_names`
- Greenhouse job-board API via `sources.greenhouse.board_tokens`
- Lever postings API via `sources.lever.companies`
- SmartRecruiters postings API via `sources.smartrecruiters.companies`
- Workable public account API via `sources.workable.account_subdomains`
- Recruitee XML feeds via `sources.recruitee.feed_urls`

Available but disabled by default:

- WorkAnywhere.pro public RSS feeds via `sources.workanywhere.feed_urls`

Enabled when free API credentials are available:

- Adzuna API with `ADZUNA_APP_ID` and `ADZUNA_APP_KEY`
- Jooble API with `JOOBLE_API_KEY`

Optional:

- The Muse API can use `THEMUSE_API_KEY`, but the source also works without it.

LinkedIn direct ingestion is a disabled placeholder until authorized API, licensed
data, or exported data access is available. Do not replace it with page scraping.

Remote OK, RemoteJobs.org, and We Work Remotely request source attribution/link-back
when their listings are displayed. The CSV keeps the source name and original job URL
for each row.
