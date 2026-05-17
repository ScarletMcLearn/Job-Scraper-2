import sqlite3
from pathlib import Path
from uuid import uuid4

from job_finder.models import JobMatch, JobPost, MatchStatus
from job_finder.storage import JobStore


def test_store_dedupes_by_canonical_url_and_exports_review_and_included() -> None:
    artifact_dir = Path(__file__).resolve().parents[1] / "test-output" / uuid4().hex
    artifact_dir.mkdir(parents=True, exist_ok=True)
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
