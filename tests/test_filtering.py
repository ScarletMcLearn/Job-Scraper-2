from job_finder.filtering import JobClassifier
from job_finder.models import JobPost, MatchStatus


def classify(title: str, description: str, location: str = "", remote: bool | None = None):
    return JobClassifier().classify(
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


def test_excludes_us_only_remote() -> None:
    match = classify(
        "QA Engineer",
        "Remote US-only role. Must be authorized to work in the United States.",
        remote=True,
    )

    assert match.status == MatchStatus.EXCLUDED
    assert "US-only remote" in match.support_evidence
