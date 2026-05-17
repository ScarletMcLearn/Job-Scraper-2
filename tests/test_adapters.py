import asyncio
import json

import httpx
import pytest

from job_finder.adapters.adzuna import AdzunaAdapter
from job_finder.adapters.arbeitnow import ArbeitnowAdapter
from job_finder.adapters.ashby import AshbyAdapter
from job_finder.adapters.greenhouse import GreenhouseAdapter
from job_finder.adapters.himalayas import HimalayasAdapter
from job_finder.adapters.jobicy import JobicyAdapter
from job_finder.adapters.jooble import JoobleAdapter
from job_finder.adapters.lever import LeverAdapter
from job_finder.adapters.recruitee import RecruiteeAdapter
from job_finder.adapters.remotejobs_org import RemoteJobsOrgAdapter
from job_finder.adapters.remoteok import RemoteOkAdapter
from job_finder.adapters.remotive import RemotiveAdapter
from job_finder.adapters.smartrecruiters import SmartRecruitersAdapter
from job_finder.adapters.themuse import TheMuseAdapter
from job_finder.adapters.weworkremotely import WeWorkRemotelyAdapter
from job_finder.adapters.workable import WorkableAdapter
from job_finder.adapters.workanywhere import WorkAnywhereAdapter
from job_finder.config import (
    AdzunaConfig,
    AppConfig,
    ArbeitnowConfig,
    AshbyConfig,
    GreenhouseConfig,
    HimalayasConfig,
    JobicyConfig,
    JoobleConfig,
    LeverConfig,
    RecruiteeConfig,
    RemoteJobsOrgConfig,
    RemoteOkConfig,
    RemotiveConfig,
    SmartRecruitersConfig,
    TheMuseConfig,
    WeWorkRemotelyConfig,
    WorkableConfig,
    WorkAnywhereConfig,
)
from job_finder.runner import build_adapters


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


def test_themuse_adapter_parses_jobs() -> None:
    async def run():
        client = httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(
                    200,
                    json={
                        "page_count": 1,
                        "results": [
                            {
                                "id": 101,
                                "name": "Quality Engineer",
                                "company": {"name": "Example"},
                                "refs": {
                                    "landing_page": "https://www.themuse.com/jobs/example/quality-engineer"
                                },
                                "locations": [{"name": "Flexible / Remote"}],
                                "contents": "<p>Remote worldwide.</p>",
                                "publication_date": "2026-01-01T00:00:00Z",
                                "categories": [{"name": "Software Engineering"}],
                                "levels": [{"name": "Mid Level"}],
                            }
                        ],
                    },
                )
            )
        )
        try:
            return await TheMuseAdapter(
                TheMuseConfig(
                    categories=["Software Engineering"],
                    locations=["Flexible / Remote"],
                    max_pages=1,
                ),
                client=client,
            ).fetch()
        finally:
            await client.aclose()

    jobs = asyncio.run(run())

    assert len(jobs) == 1
    assert jobs[0].source == "themuse"
    assert jobs[0].title == "Quality Engineer"
    assert jobs[0].remote is True


def test_adzuna_adapter_parses_jobs() -> None:
    async def run():
        client = httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(
                    200,
                    json={
                        "results": [
                            {
                                "id": "adz-1",
                                "title": "QA Engineer",
                                "company": {"display_name": "Example"},
                                "redirect_url": "https://example.com/adzuna/qa",
                                "location": {"display_name": "Remote, United Kingdom"},
                                "description": "Remote worldwide. Visa support.",
                                "created": "2026-01-01T00:00:00Z",
                                "category": {"label": "IT Jobs"},
                                "contract_time": "full_time",
                            }
                        ]
                    },
                )
            )
        )
        try:
            return await AdzunaAdapter(
                AdzunaConfig(
                    search_terms=["qa"],
                    country_codes=["gb"],
                    locations=["remote"],
                    max_pages=1,
                    results_per_page=1,
                ),
                "app-id",
                "app-key",
                client,
            ).fetch()
        finally:
            await client.aclose()

    jobs = asyncio.run(run())

    assert len(jobs) == 1
    assert jobs[0].source == "adzuna"
    assert jobs[0].company == "Example"
    assert jobs[0].remote is True


def test_jooble_adapter_parses_jobs() -> None:
    async def run():
        client = httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(
                    200,
                    json={
                        "jobs": [
                            {
                                "id": "job-1",
                                "title": "Manual Tester",
                                "company": "Example",
                                "link": "https://example.com/jooble/manual-tester",
                                "location": "Remote",
                                "snippet": "Remote worldwide testing role.",
                                "updated": "2026-01-01T00:00:00Z",
                                "source": "Example Feed",
                            }
                        ]
                    },
                )
            )
        )
        try:
            return await JoobleAdapter(
                JoobleConfig(
                    search_terms=["manual tester"],
                    locations=["Remote"],
                    max_pages=1,
                    results_per_page=1,
                ),
                "api-key",
                client,
            ).fetch()
        finally:
            await client.aclose()

    jobs = asyncio.run(run())

    assert len(jobs) == 1
    assert jobs[0].source == "jooble"
    assert jobs[0].title == "Manual Tester"
    assert jobs[0].remote is True


def test_workable_adapter_parses_jobs() -> None:
    async def run():
        client = httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(
                    200,
                    json={
                        "name": "Example",
                        "jobs": [
                            {
                                "id": "workable-1",
                                "title": "Automation Engineer",
                                "url": "https://apply.workable.com/example/j/workable-1/",
                                "location": {
                                    "location_str": "Remote",
                                    "telecommuting": True,
                                },
                                "description": "Remote worldwide.",
                                "requirements": "Playwright preferred.",
                                "created_at": "2026-01-01T00:00:00Z",
                            }
                        ],
                    },
                )
            )
        )
        try:
            return await WorkableAdapter(
                WorkableConfig(account_subdomains=["example"]),
                client,
            ).fetch()
        finally:
            await client.aclose()

    jobs = asyncio.run(run())

    assert len(jobs) == 1
    assert jobs[0].source == "workable"
    assert jobs[0].company == "Example"
    assert jobs[0].remote is True


def test_recruitee_adapter_parses_feed_jobs() -> None:
    async def run():
        feed = """<?xml version="1.0" encoding="UTF-8"?>
        <jobs>
          <job>
            <reference>rec-1</reference>
            <title>Software Quality Engineer</title>
            <company>Example</company>
            <url>https://example.com/recruitee/software-quality-engineer</url>
            <remote>true</remote>
            <city>Remote</city>
            <country>Worldwide</country>
            <description_requirements><![CDATA[Remote worldwide.]]></description_requirements>
            <posted>2026-01-01T00:00:00Z</posted>
          </job>
        </jobs>
        """
        client = httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, content=feed)
            )
        )
        try:
            return await RecruiteeAdapter(
                RecruiteeConfig(feed_urls=["https://example.com/feed.xml"]),
                client,
            ).fetch()
        finally:
            await client.aclose()

    jobs = asyncio.run(run())

    assert len(jobs) == 1
    assert jobs[0].source == "recruitee"
    assert jobs[0].location == "Remote, Worldwide"
    assert jobs[0].remote is True


def test_workanywhere_adapter_parses_rss_items() -> None:
    async def run():
        rss = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
          <channel>
            <item>
              <title>Example: QA Analyst</title>
              <link>https://workanywhere.pro/jobs/example-qa-analyst</link>
              <guid>wa-1</guid>
              <pubDate>Thu, 01 Jan 2026 00:00:00 +0000</pubDate>
              <description><![CDATA[Work from anywhere.]]></description>
              <category>Engineering</category>
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
            return await WorkAnywhereAdapter(
                WorkAnywhereConfig(feed_urls=["https://example.com/feed.xml"]),
                client,
            ).fetch()
        finally:
            await client.aclose()

    jobs = asyncio.run(run())

    assert len(jobs) == 1
    assert jobs[0].source == "workanywhere"
    assert jobs[0].company == "Example"
    assert jobs[0].title == "QA Analyst"
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


def test_build_adapters_reports_missing_key_sources_as_skipped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ADZUNA_APP_ID", raising=False)
    monkeypatch.delenv("ADZUNA_APP_KEY", raising=False)
    monkeypatch.delenv("JOOBLE_API_KEY", raising=False)

    adapters = build_adapters(AppConfig())
    adapters_by_name = {adapter.name: adapter for adapter in adapters}

    assert adapters_by_name["adzuna"].__class__.__name__ == "SkippedSourceAdapter"
    assert adapters_by_name["jooble"].__class__.__name__ == "SkippedSourceAdapter"


def test_build_adapters_uses_key_sources_when_credentials_exist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ADZUNA_APP_ID", "app-id")
    monkeypatch.setenv("ADZUNA_APP_KEY", "app-key")
    monkeypatch.setenv("JOOBLE_API_KEY", "api-key")

    adapters = build_adapters(AppConfig())
    adapters_by_name = {adapter.name: adapter for adapter in adapters}

    assert adapters_by_name["adzuna"].__class__.__name__ == "AdzunaAdapter"
    assert adapters_by_name["jooble"].__class__.__name__ == "JoobleAdapter"


def test_build_adapters_omits_disabled_key_sources() -> None:
    config = AppConfig()
    config.sources.adzuna.enabled = False
    config.sources.jooble.enabled = False

    adapter_names = {adapter.name for adapter in build_adapters(config)}

    assert "adzuna" not in adapter_names
    assert "jooble" not in adapter_names
