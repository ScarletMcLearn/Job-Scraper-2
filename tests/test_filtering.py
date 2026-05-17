from typing import Literal

import pytest

from job_finder.config import FilterConfig
from job_finder.filtering import JobClassifier
from job_finder.models import JobMatch, JobPost, MatchStatus

Strictness = Literal["strict", "evidence", "broad", "lenient", "discovery"]


def classify(
    title: str,
    description: str,
    location: str = "",
    remote: bool | None = None,
    strictness: Strictness = "evidence",
) -> JobMatch:
    return JobClassifier(FilterConfig(strictness=strictness)).classify(
        JobPost(
            source="test",
            source_id="1",
            title=title,
            company="Example",
            url="https://example.com/jobs/1",
            location=location,
            remote=remote,
            description=description,
        )
    )


def test_includes_role_with_visa_support() -> None:
    match = classify(
        "SDET Engineer",
        "We provide visa sponsorship and immigration support for the right candidate.",
    )

    assert match.status == MatchStatus.INCLUDED
    assert "SDET" in match.matched_keywords
    assert "visa sponsorship" in match.support_evidence


def test_includes_worldwide_remote_role() -> None:
    match = classify(
        "QA Automation Engineer",
        "Fully remote role open worldwide. Selenium experience is useful.",
        remote=True,
    )

    assert match.status == MatchStatus.INCLUDED
    assert "worldwide remote" in match.support_evidence


@pytest.mark.parametrize(
    ("title", "expected_keyword"),
    [
        ("QA Analyst", "QA"),
        ("Quality Engineer", "Quality Engineer"),
        ("Software Quality Engineer", "Quality Engineer"),
        ("Test Engineer", "Test"),
        ("Manual Tester", "Test"),
        ("Automation Engineer", "Automation"),
    ],
)
def test_includes_expanded_qa_title_variants(
    title: str,
    expected_keyword: str,
) -> None:
    match = classify(
        title,
        "Fully remote role open worldwide.",
        remote=True,
    )

    assert match.status == MatchStatus.INCLUDED
    assert expected_keyword in match.matched_keywords


def test_review_for_remote_without_geography() -> None:
    match = classify(
        "Quality Assurance Analyst",
        "Remote role for a product team.",
        remote=True,
    )

    assert match.status == MatchStatus.REVIEW
    assert "remote role needs manual geography verification" in match.reasons


def test_excludes_no_sponsorship_without_remote() -> None:
    match = classify(
        "Software Tester",
        "No visa sponsorship is available and relocation is not offered.",
    )

    assert match.status == MatchStatus.EXCLUDED
    assert "no visa sponsorship" in match.support_evidence


def test_excludes_non_qa_role() -> None:
    match = classify(
        "Backend Engineer",
        "Visa sponsorship is available.",
    )

    assert match.status == MatchStatus.EXCLUDED
    assert "role keyword mismatch" in match.reasons


def test_excludes_non_qa_title_even_when_description_mentions_testing() -> None:
    match = classify(
        "Office Assistant",
        "This role coordinates quality assurance reviews and test schedules. Remote worldwide.",
        remote=True,
    )

    assert match.status == MatchStatus.EXCLUDED
    assert "role keyword only found outside title" in match.reasons


def test_excludes_us_only_remote() -> None:
    match = classify(
        "QA Engineer",
        "Remote US-only role. Must be authorized to work in the United States.",
        remote=True,
    )

    assert match.status == MatchStatus.EXCLUDED
    assert "US-only remote" in match.support_evidence


def test_strict_excludes_remote_without_geography() -> None:
    match = classify(
        "Quality Assurance Analyst",
        "Remote role for a product team.",
        remote=True,
        strictness="strict",
    )

    assert match.status == MatchStatus.EXCLUDED


def test_broad_includes_remote_without_geography() -> None:
    match = classify(
        "Quality Assurance Analyst",
        "Remote role for a product team.",
        remote=True,
        strictness="broad",
    )

    assert match.status == MatchStatus.INCLUDED


def test_lenient_reviews_role_with_no_support_or_remote_evidence() -> None:
    match = classify(
        "QA Engineer",
        "Build regression suites for a product team.",
        strictness="lenient",
    )

    assert match.status == MatchStatus.REVIEW
    assert "no visa, relocation, or eligible remote evidence" in match.reasons


def test_lenient_accepts_description_only_role_signal_for_review() -> None:
    match = classify(
        "Office Assistant",
        "This role coordinates quality assurance reviews and test schedules.",
        strictness="lenient",
    )

    assert match.status == MatchStatus.REVIEW
    assert "role keyword only found outside title" in match.reasons


def test_lenient_includes_description_only_remote_role() -> None:
    match = classify(
        "Office Assistant",
        "This role coordinates quality assurance reviews and test schedules. Remote role.",
        remote=True,
        strictness="lenient",
    )

    assert match.status == MatchStatus.INCLUDED
    assert "role keyword only found outside title" in match.reasons


def test_discovery_includes_qa_role_with_weak_evidence() -> None:
    match = classify(
        "QA Engineer",
        "Build regression suites for a product team.",
        strictness="discovery",
    )

    assert match.status == MatchStatus.INCLUDED
    assert "included by discovery mode despite weak support evidence" in match.reasons


def test_discovery_still_excludes_us_only_remote() -> None:
    match = classify(
        "QA Engineer",
        "Remote US-only role. Must be authorized to work in the United States.",
        remote=True,
        strictness="discovery",
    )

    assert match.status == MatchStatus.EXCLUDED
    assert "US-only remote" in match.support_evidence
