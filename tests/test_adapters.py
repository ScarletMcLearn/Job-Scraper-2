import asyncio
import json

import httpx

from job_finder.adapters.arbeitnow import ArbeitnowAdapter
from job_finder.adapters.greenhouse import GreenhouseAdapter
from job_finder.adapters.lever import LeverAdapter
from job_finder.adapters.remotive import RemotiveAdapter
from job_finder.config import ArbeitnowConfig, GreenhouseConfig, LeverConfig, RemotiveConfig


def test_remotive_adapter_parses_jobs() -> None:
    async def run():
        client = httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(
                    200,
                    json={
                        "jobs": [
                            {
                                "id": 123,
                                "title": "QA Engineer",
                                "company_name": "Example",
                                "url": "https://example.com/qa",
                                "candidate_required_location": "Worldwide",
                                "description": "Remote worldwide",
                                "publication_date": "2026-01-01T00:00:00Z",
                            }
                        ]
                    },
                )
            )
        )
        try:
            return await RemotiveAdapter(RemotiveConfig(search_terms=["qa"]), client).fetch()
        finally:
            await client.aclose()

    jobs = asyncio.run(run())

    assert len(jobs) == 1
    assert jobs[0].source == "remotive"
    assert jobs[0].remote is True


def test_arbeitnow_adapter_parses_jobs() -> None:
    async def run():
        client = httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(
                    200,
                    json={
                        "data": [
                            {
                                "slug": "qa-engineer",
                                "title": "QA Engineer",
                                "company_name": "Example",
                                "url": "https://example.com/qa",
                                "location": "Berlin",
                                "remote": True,
                                "description": "Remote APAC possible",
                                "created_at": 1767225600,
                                "tags": ["Remote"],
                            }
                        ]
                    },
                )
            )
        )
        try:
            return await ArbeitnowAdapter(ArbeitnowConfig(max_pages=1), client).fetch()
        finally:
            await client.aclose()

    jobs = asyncio.run(run())

    assert len(jobs) == 1
    assert jobs[0].source_id == "qa-engineer"
    assert jobs[0].remote is True


def test_greenhouse_adapter_parses_jobs() -> None:
    async def run():
        client = httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(
                    200,
                    json={
                        "jobs": [
                            {
                                "id": 99,
                                "title": "SDET",
                                "absolute_url": "https://boards.greenhouse.io/example/jobs/99",
                                "location": {"name": "Remote"},
                                "content": "<p>Visa sponsorship available.</p>",
                                "updated_at": "2026-01-01T00:00:00Z",
                            }
                        ]
                    },
                )
            )
        )
        try:
            return await GreenhouseAdapter(GreenhouseConfig(board_tokens=["example"]), client).fetch()
        finally:
            await client.aclose()

    jobs = asyncio.run(run())

    assert len(jobs) == 1
    assert jobs[0].company == "example"
    assert jobs[0].title == "SDET"


def test_lever_adapter_parses_jobs() -> None:
    async def run():
        payload = [
            {
                "id": "abc",
                "text": "QA Automation Engineer",
                "hostedUrl": "https://jobs.lever.co/example/abc",
                "categories": {"location": "Remote"},
                "description": "Work from anywhere.",
                "additional": "Relocation support available.",
                "lists": [{"content": "Playwright preferred."}],
                "createdAt": 1767225600000,
            }
        ]
        client = httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, content=json.dumps(payload).encode())
            )
        )
        try:
            return await LeverAdapter(LeverConfig(companies=["example"]), client).fetch()
        finally:
            await client.aclose()

    jobs = asyncio.run(run())

    assert len(jobs) == 1
    assert jobs[0].remote is True
    assert "Playwright" in jobs[0].description
