import sqlite3
from pathlib import Path
from uuid import uuid4

from job_finder.models import JobMatch, JobPost, MatchStatus
from job_finder.storage import JobStore


def test_store_dedupes_by_canonical_url_and_exports_review_and_included() -> None:
    artifact_dir = _artifact_dir()
    db_path = artifact_dir / "jobs.sqlite"
    csv_path = artifact_dir / "jobs.csv"
    store = JobStore(db_path)

    try:
        run_id = store.start_run()
        job = JobPost(
            source="test",
            source_id="1",
            title="QA Engineer",
            company="Example",
            url="https://example.com/jobs/1?utm_source=x",
            location="Remote worldwide",
            remote=True,
            description="Remote worldwide.",
        )
        store.upsert_match(
            run_id,
            JobMatch(
                job=job,
                status=MatchStatus.INCLUDED,
                matched_keywords=["QA"],
                support_evidence=["worldwide remote"],
                reasons=["remote eligible"],
            ),
        )
        job.url = "https://example.com/jobs/1"
        store.upsert_match(
            run_id,
            JobMatch(
                job=job,
                status=MatchStatus.REVIEW,
                matched_keywords=["QA"],
                support_evidence=["remote"],
                reasons=["manual review"],
            ),
        )
        exported = store.export_csv(csv_path)
    finally:
        store.close()

    assert exported == 1
    assert "manual review" in csv_path.read_text(encoding="utf-8")

    connection = sqlite3.connect(db_path)
    try:
        count = connection.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    finally:
        connection.close()

    assert count == 1


def test_store_exports_markdown_report_with_default_statuses() -> None:
    artifact_dir = _artifact_dir()
    db_path = artifact_dir / "jobs.sqlite"
    markdown_path = artifact_dir / "nested" / "jobs.md"
    store = JobStore(db_path)

    try:
        run_id = store.start_run()
        included_job = JobPost(
            source="Remote OK",
            source_id="1",
            title="QA Engineer",
            company="Example",
            url="https://example.com/jobs/1?utm_source=x",
            location="Remote worldwide",
            remote=True,
            description="Remote worldwide.",
        )
        excluded_job = JobPost(
            source="test",
            source_id="2",
            title="Backend Engineer",
            company="Example",
            url="https://example.com/jobs/2",
            location="Berlin",
            remote=False,
            description="No QA evidence.",
        )
        store.upsert_match(
            run_id,
            JobMatch(
                job=included_job,
                status=MatchStatus.INCLUDED,
                matched_keywords=["QA"],
                support_evidence=["worldwide remote"],
                reasons=["remote eligible"],
            ),
        )
        store.upsert_match(
            run_id,
            JobMatch(
                job=excluded_job,
                status=MatchStatus.EXCLUDED,
                matched_keywords=[],
                support_evidence=[],
                reasons=["no role keyword"],
            ),
        )
        exported = store.export_markdown(markdown_path)
    finally:
        store.close()

    report = markdown_path.read_text(encoding="utf-8")
    assert exported == 1
    assert markdown_path.exists()
    assert "# Job Search Results" in report
    assert "- Included: 1" in report
    assert "- Review: 0" in report
    assert "## Included" in report
    assert "## Review" in report
    assert "[QA Engineer](https://example.com/jobs/1?utm_source=x)" in report
    assert "Remote OK" in report
    assert "worldwide remote" in report
    assert "QA" in report
    assert "remote eligible" in report
    assert "Backend Engineer" not in report


def _artifact_dir() -> Path:
    path = Path(__file__).resolve().parents[1] / "artifacts" / "tests" / uuid4().hex
    path.mkdir(parents=True, exist_ok=True)
    return path
