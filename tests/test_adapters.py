import asyncio
import json

import httpx

from job_finder.adapters.arbeitnow import ArbeitnowAdapter
from job_finder.adapters.ashby import AshbyAdapter
from job_finder.adapters.greenhouse import GreenhouseAdapter
from job_finder.adapters.himalayas import HimalayasAdapter
from job_finder.adapters.jobicy import JobicyAdapter
from job_finder.adapters.lever import LeverAdapter
from job_finder.adapters.remotejobs_org import RemoteJobsOrgAdapter
from job_finder.adapters.remoteok import RemoteOkAdapter
from job_finder.adapters.remotive import RemotiveAdapter
from job_finder.adapters.smartrecruiters import SmartRecruitersAdapter
from job_finder.adapters.weworkremotely import WeWorkRemotelyAdapter
from job_finder.config import (
    ArbeitnowConfig,
    AshbyConfig,
    GreenhouseConfig,
    HimalayasConfig,
    JobicyConfig,
    LeverConfig,
    RemoteJobsOrgConfig,
    RemoteOkConfig,
    RemotiveConfig,
    SmartRecruitersConfig,
    WeWorkRemotelyConfig,
)


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
            return await RemotiveAdapter(
                RemotiveConfig(search_terms=["qa"]), client
            ).fetch()
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
            return await GreenhouseAdapter(
                GreenhouseConfig(board_tokens=["example"]), client
            ).fetch()
        finally:
            await client.aclose()

    jobs = asyncio.run(run())

    assert len(jobs) == 1
    assert jobs[0].company == "example"
    assert jobs[0].title == "SDET"


def test_himalayas_adapter_parses_jobs() -> None:
    async def run():
        client = httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(
                    200,
                    json={
                        "jobs": [
                            {
                                "guid": "him-1",
                                "title": "QA Engineer",
                                "companyName": "Example",
                                "applicationLink": "https://example.com/himalayas/qa",
                                "locationRestrictions": [],
                                "description": "<p>Remote worldwide.</p>",
                                "pubDate": 1767225600000,
                            }
                        ]
                    },
                )
            )
        )
        try:
            return await HimalayasAdapter(
                HimalayasConfig(search_terms=["qa"], max_pages=1), client
            ).fetch()
        finally:
            await client.aclose()

    jobs = asyncio.run(run())

    assert len(jobs) == 1
    assert jobs[0].source == "himalayas"
    assert jobs[0].location == "Worldwide"
    assert jobs[0].remote is True


def test_jobicy_adapter_parses_jobs() -> None:
    async def run():
        client = httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(
                    200,
                    json={
                        "jobs": [
                            {
                                "id": 456,
                                "jobTitle": "SDET",
                                "companyName": "Example",
                                "url": "https://example.com/jobicy/sdet",
                                "jobGeo": "Anywhere",
                                "jobDescription": "<p>Remote role.</p>",
                                "pubDate": "2026-01-01T00:00:00+00:00",
                            }
                        ]
                    },
                )
            )
        )
        try:
            return await JobicyAdapter(
                JobicyConfig(search_terms=["sdet"], count=1), client
            ).fetch()
        finally:
            await client.aclose()

    jobs = asyncio.run(run())

    assert len(jobs) == 1
    assert jobs[0].source == "jobicy"
    assert jobs[0].title == "SDET"
    assert jobs[0].remote is True


def test_jobicy_adapter_skips_bad_request_terms() -> None:
    async def run():
        requested_tags: list[str | None] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requested_tags.append(request.url.params.get("tag"))
            if request.url.params.get("tag") == "qa":
                return httpx.Response(400)
            return httpx.Response(
                200,
                json={
                    "jobs": [
                        {
                            "id": 456,
                            "jobTitle": "SDET",
                            "companyName": "Example",
                            "url": "https://example.com/jobicy/sdet",
                            "jobGeo": "Anywhere",
                            "jobDescription": "<p>Remote role.</p>",
                            "pubDate": "2026-01-01T00:00:00+00:00",
                        }
                    ]
                },
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        try:
            jobs = await JobicyAdapter(
                JobicyConfig(search_terms=["qa", "sdet"], count=1), client
            ).fetch()
            return requested_tags, jobs
        finally:
            await client.aclose()

    requested_tags, jobs = asyncio.run(run())

    assert requested_tags == ["qa", "sdet"]
    assert len(jobs) == 1
    assert jobs[0].title == "SDET"


def test_remoteok_adapter_parses_jobs_and_skips_metadata() -> None:
    async def run():
        client = httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(
                    200,
                    json=[
                        {"legal": "metadata row"},
                        {
                            "id": 789,
                            "slug": "remote-qa-engineer-example-789",
                            "position": "QA Engineer",
                            "company": "Example",
                            "url": "https://remoteok.com/remote-jobs/remote-qa-engineer-example-789",
                            "location": "Worldwide",
                            "description": "<p>Work from anywhere.</p>",
                            "date": "2026-01-01T00:00:00+00:00",
                            "tags": ["testing", "automation"],
                        },
                    ],
                )
            )
        )
        try:
            return await RemoteOkAdapter(RemoteOkConfig(max_results=10), client).fetch()
        finally:
            await client.aclose()

    jobs = asyncio.run(run())

    assert len(jobs) == 1
    assert jobs[0].source == "remoteok"
    assert jobs[0].title == "QA Engineer"
    assert jobs[0].remote is True
    assert "automation" in jobs[0].description


def test_remotejobs_org_adapter_parses_jobs() -> None:
    async def run():
        client = httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(
                    200,
                    json={
                        "data": [
                            {
                                "id": "rj-1",
                                "title": "SDET",
                                "url": "https://remotejobs.org/remote-jobs/sdet-example",
                                "company": {"name": "Example"},
                                "category": {"name": "Quality Assurance"},
                                "location": "Remote (Worldwide)",
                                "type": "Full-time",
                                "description": "Remote worldwide.",
                                "posted_at": "2026-01-01T00:00:00Z",
                            }
                        ],
                        "pagination": {"has_more": False},
                    },
                )
            )
        )
        try:
            return await RemoteJobsOrgAdapter(
                RemoteJobsOrgConfig(search_terms=["qa"], limit=1, max_pages=1), client
            ).fetch()
        finally:
            await client.aclose()

    jobs = asyncio.run(run())

    assert len(jobs) == 1
    assert jobs[0].source == "remotejobs_org"
    assert jobs[0].company == "Example"
    assert jobs[0].location == "Remote (Worldwide)"


def test_weworkremotely_adapter_parses_rss_items() -> None:
    async def run():
        rss = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
          <channel>
            <item>
              <title>Example: QA Automation Engineer</title>
              <link>https://weworkremotely.com/remote-jobs/example-qa-automation-engineer</link>
              <guid>wwr-1</guid>
              <pubDate>Thu, 01 Jan 2026 00:00:00 +0000</pubDate>
              <description><![CDATA[Remote worldwide. Playwright preferred.]]></description>
              <category>Programming</category>
            </item>
          </channel>
        </rss>
        """
        client = httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, content=rss)
            )
        )
        try:
            return await WeWorkRemotelyAdapter(
                WeWorkRemotelyConfig(feed_urls=["https://example.com/jobs.rss"]), client
            ).fetch()
        finally:
            await client.aclose()

    jobs = asyncio.run(run())

    assert len(jobs) == 1
    assert jobs[0].source == "weworkremotely"
    assert jobs[0].company == "Example"
    assert jobs[0].title == "QA Automation Engineer"
    assert jobs[0].remote is True


def test_ashby_adapter_parses_jobs() -> None:
    async def run():
        client = httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(
                    200,
                    json={
                        "jobs": [
                            {
                                "id": "ashby-1",
                                "title": "QA Engineer",
                                "location": "Remote",
                                "secondaryLocations": [{"location": "Bangladesh"}],
                                "isRemote": True,
                                "workplaceType": "Remote",
                                "descriptionHtml": "<p>Remote worldwide.</p>",
                                "publishedAt": "2026-01-01T00:00:00Z",
                                "jobUrl": "https://jobs.ashbyhq.com/example/ashby-1",
                                "isListed": True,
                            }
                        ]
                    },
                )
            )
        )
        try:
            return await AshbyAdapter(
                AshbyConfig(organization_names=["example"]), client
            ).fetch()
        finally:
            await client.aclose()

    jobs = asyncio.run(run())

    assert len(jobs) == 1
    assert jobs[0].source == "ashby"
    assert jobs[0].company == "example"
    assert jobs[0].location == "Remote, Bangladesh"
    assert jobs[0].remote is True


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
                lambda request: httpx.Response(
                    200, content=json.dumps(payload).encode()
                )
            )
        )
        try:
            return await LeverAdapter(
                LeverConfig(companies=["example"]), client
            ).fetch()
        finally:
            await client.aclose()

    jobs = asyncio.run(run())

    assert len(jobs) == 1
    assert jobs[0].remote is True
    assert "Playwright" in jobs[0].description


def test_smartrecruiters_adapter_parses_jobs_with_details() -> None:
    async def run():
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith("/postings/sr-1"):
                return httpx.Response(
                    200,
                    json={
                        "id": "sr-1",
                        "name": "QA Engineer",
                        "company": {"name": "Example"},
                        "applyUrl": "https://jobs.smartrecruiters.com/example/sr-1",
                        "releasedDate": "2026-01-01T00:00:00Z",
                        "location": {"city": "Remote", "country": "BD", "remote": True},
                        "jobAd": {
                            "sections": {
                                "jobDescription": {
                                    "text": "Remote worldwide. Visa sponsorship available."
                                }
                            }
                        },
                    },
                )
            return httpx.Response(
                200,
                json={
                    "content": [
                        {
                            "id": "sr-1",
                            "name": "QA Engineer",
                            "company": {"name": "Example"},
                            "ref": "https://api.smartrecruiters.com/v1/companies/example/postings/sr-1",
                            "releasedDate": "2026-01-01T00:00:00Z",
                            "location": {"remote": True},
                        }
                    ]
                },
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        try:
            return await SmartRecruitersAdapter(
                SmartRecruitersConfig(
                    companies=["example"], search_terms=["qa"], limit=1
                ),
                client,
            ).fetch()
        finally:
            await client.aclose()

    jobs = asyncio.run(run())

    assert len(jobs) == 1
    assert jobs[0].source == "smartrecruiters"
    assert jobs[0].url == "https://jobs.smartrecruiters.com/example/sr-1"
    assert jobs[0].remote is True
    assert "Visa sponsorship" in jobs[0].description
