# Repository Guidelines

## Project Shape

This is a Python 3.13 CLI package named `job-finder`. Source code lives in
`src/job_finder`, tests live in `tests`, and the default runtime configuration is
`config/search.yml`.

The CLI finds QA/Test/SQA/SDET/automation jobs with visa, relocation, or
Bangladesh-eligible remote evidence. It stores scan results in SQLite and exports
CSV output.

## Commands

Use `uv` with the local cache directory so dependency and test artifacts stay in
the workspace:

```powershell
uv --cache-dir .uv-cache sync
uv --cache-dir .uv-cache run pytest
uv --cache-dir .uv-cache run job-finder scan --config config/search.yml
uv --cache-dir .uv-cache run job-finder export --config config/search.yml
uv --cache-dir .uv-cache run job-finder linkedin-searches
```

## Generated Artifacts

Treat these paths as local/generated output, not source:

- `data/`
- `output/`
- `.uv-cache/`
- `.pytest-tmp/`
- `.venv/`
- `pytest-cache-files-*/`
- Python `__pycache__/` directories

Do not commit generated SQLite databases, CSV exports, virtual environments,
caches, logs, or local environment files.

## LinkedIn Guardrail

Do not add direct LinkedIn scraping. LinkedIn support must stay limited to
manual search URL generation unless the project is given authorized API access,
licensed data, or exported data access. Preserve this compliance-first behavior
when changing CLI commands, adapters, or documentation.

## Implementation Guidance

Follow the existing adapter pattern under `src/job_finder/adapters`. New sources
should implement the `JobSourceAdapter` interface, normalize results into
`JobPost`, and be wired through `build_adapters` only when their config is
enabled and complete.

When changing filtering, storage, adapter parsing, URL canonicalization, or CSV
export behavior, add or update focused tests under `tests`. Keep dependencies
pinned exactly in `pyproject.toml`.

Exports must preserve source names and original job URLs because some upstream
sources request attribution or link-back when listings are displayed.
