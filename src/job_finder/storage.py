from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from job_finder.models import JobMatch, MatchStatus, now_utc


CSV_COLUMNS = [
    "status",
    "title",
    "company",
    "location",
    "remote",
    "support_evidence",
    "matched_keywords",
    "reasons",
    "source",
    "url",
    "published_at",
    "first_seen_at",
    "last_seen_at",
]


class JobStore:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.database_path)
        self.connection.row_factory = sqlite3.Row
        self._migrate()

    def close(self) -> None:
        self.connection.close()

    def start_run(self) -> int:
        now = now_utc().isoformat()
        cursor = self.connection.execute(
            "INSERT INTO runs (started_at, completed_at) VALUES (?, NULL)",
            (now,),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def complete_run(self, run_id: int) -> None:
        self.connection.execute(
            "UPDATE runs SET completed_at = ? WHERE id = ?",
            (now_utc().isoformat(), run_id),
        )
        self.connection.commit()

    def upsert_match(self, run_id: int, match: JobMatch) -> None:
        job = match.job
        now = now_utc().isoformat()
        published_at = job.published_at.isoformat() if job.published_at else None
        canonical_url = canonicalize_url(job.url)
        self.connection.execute(
            """
            INSERT INTO jobs (
                source, source_id, canonical_url, url, title, company, location, remote,
                description, published_at, status, matched_keywords, support_evidence,
                reasons, raw, first_seen_at, last_seen_at, last_seen_run_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(canonical_url) DO UPDATE SET
                source = excluded.source,
                source_id = excluded.source_id,
                url = excluded.url,
                title = excluded.title,
                company = excluded.company,
                location = excluded.location,
                remote = excluded.remote,
                description = excluded.description,
                published_at = excluded.published_at,
                status = excluded.status,
                matched_keywords = excluded.matched_keywords,
                support_evidence = excluded.support_evidence,
                reasons = excluded.reasons,
                raw = excluded.raw,
                last_seen_at = excluded.last_seen_at,
                last_seen_run_id = excluded.last_seen_run_id
            """,
            (
                job.source,
                job.source_id,
                canonical_url,
                job.url,
                job.title,
                job.company,
                job.location,
                None if job.remote is None else int(job.remote),
                job.description,
                published_at,
                match.status.value,
                json.dumps(match.matched_keywords, ensure_ascii=True),
                json.dumps(match.support_evidence, ensure_ascii=True),
                json.dumps(match.reasons, ensure_ascii=True),
                json.dumps(job.raw, ensure_ascii=True, default=str),
                now,
                now,
                run_id,
            ),
        )
        self.connection.commit()

    def export_csv(
        self,
        csv_path: Path,
        statuses: tuple[MatchStatus, ...] = (MatchStatus.INCLUDED, MatchStatus.REVIEW),
    ) -> int:
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        rows = self.connection.execute(
            f"""
            SELECT status, title, company, location, remote, support_evidence,
                   matched_keywords, reasons, source, url, published_at,
                   first_seen_at, last_seen_at
            FROM jobs
            WHERE status IN ({",".join("?" for _ in statuses)})
            ORDER BY
                CASE status WHEN 'included' THEN 0 WHEN 'review' THEN 1 ELSE 2 END,
                published_at DESC,
                last_seen_at DESC
            """,
            tuple(status.value for status in statuses),
        ).fetchall()

        with csv_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            for row in rows:
                writer.writerow(
                    {
                        "status": row["status"],
                        "title": row["title"],
                        "company": row["company"],
                        "location": row["location"],
                        "remote": _bool_label(row["remote"]),
                        "support_evidence": _json_list_to_text(row["support_evidence"]),
                        "matched_keywords": _json_list_to_text(row["matched_keywords"]),
                        "reasons": _json_list_to_text(row["reasons"]),
                        "source": row["source"],
                        "url": row["url"],
                        "published_at": row["published_at"] or "",
                        "first_seen_at": row["first_seen_at"],
                        "last_seen_at": row["last_seen_at"],
                    }
                )
        return len(rows)

    def _migrate(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TEXT NOT NULL,
                completed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                source_id TEXT,
                canonical_url TEXT NOT NULL UNIQUE,
                url TEXT NOT NULL,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT,
                remote INTEGER,
                description TEXT,
                published_at TEXT,
                status TEXT NOT NULL,
                matched_keywords TEXT NOT NULL,
                support_evidence TEXT NOT NULL,
                reasons TEXT NOT NULL,
                raw TEXT NOT NULL,
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                last_seen_run_id INTEGER NOT NULL,
                FOREIGN KEY(last_seen_run_id) REFERENCES runs(id)
            );

            CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
            CREATE INDEX IF NOT EXISTS idx_jobs_source_id ON jobs(source, source_id);
            CREATE INDEX IF NOT EXISTS idx_jobs_last_seen_run_id ON jobs(last_seen_run_id);
            """
        )
        self.connection.commit()


def canonicalize_url(url: str) -> str:
    split = urlsplit(url)
    query = [
        (key, value)
        for key, value in parse_qsl(split.query, keep_blank_values=True)
        if not key.lower().startswith("utm_")
    ]
    clean_query = urlencode(query, doseq=True)
    return urlunsplit(
        (
            split.scheme.lower(),
            split.netloc.lower(),
            split.path.rstrip("/") or "/",
            clean_query,
            "",
        )
    )


def _json_list_to_text(value: str) -> str:
    try:
        parsed = json.loads(value or "[]")
    except json.JSONDecodeError:
        return value
    if not isinstance(parsed, list):
        return str(parsed)
    return "; ".join(str(item) for item in parsed)


def _bool_label(value: int | None) -> str:
    if value is None:
        return ""
    return "true" if bool(value) else "false"
