import csv
import io
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


DATABASE_PATH = Path(__file__).resolve().parent / "placements.db"
APPLICATION_STATUSES = [
    "Applied",
    "Shortlisted",
    "Interview Scheduled",
    "Selected",
    "Rejected",
]
APPLICATION_COLUMNS = (
    "application_id",
    "company_name",
    "job_role",
    "application_date",
    "status",
    "interview_date",
)


@contextmanager
def _connection() -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize_database() -> None:
    """Create the applications table and add new columns to older databases."""
    with _connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS applications (
                application_id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                job_role TEXT NOT NULL,
                application_date TEXT,
                status TEXT
            )
            """
        )
        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(applications)")
        }
        if "interview_date" not in columns:
            connection.execute(
                "ALTER TABLE applications ADD COLUMN interview_date TEXT"
            )


def add_application(
    company_name: str,
    job_role: str,
    application_date: str,
    status: str,
    interview_date: str | None = None,
) -> None:
    with _connection() as connection:
        connection.execute(
            """
            INSERT INTO applications
                (company_name, job_role, application_date, status, interview_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (company_name, job_role, application_date, status, interview_date),
        )


def get_applications(
    company_name: str = "",
    status: str | None = None,
) -> list[dict[str, object]]:
    conditions = []
    parameters: list[str] = []
    if company_name.strip():
        conditions.append("instr(lower(company_name), lower(?)) > 0")
        parameters.append(company_name.strip())
    if status is not None:
        conditions.append("status = ?")
        parameters.append(status)
    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    with _connection() as connection:
        rows = connection.execute(
            f"""
            SELECT application_id, company_name, job_role, application_date,
                   status, interview_date
            FROM applications
            {where_clause}
            ORDER BY application_date DESC, application_id DESC
            """,
            parameters,
        ).fetchall()
    return [dict(row) for row in rows]


def get_statuses() -> list[str]:
    with _connection() as connection:
        rows = connection.execute(
            """
            SELECT DISTINCT status
            FROM applications
            WHERE status IS NOT NULL AND status <> ''
            ORDER BY status COLLATE NOCASE, status
            """
        ).fetchall()
    return [row["status"] for row in rows]


def update_application(
    application_id: int,
    status: str,
    interview_date: str | None,
) -> bool:
    if status not in APPLICATION_STATUSES and status not in get_statuses():
        raise ValueError(f"Unsupported application status: {status}")
    with _connection() as connection:
        cursor = connection.execute(
            """
            UPDATE applications
            SET status = ?, interview_date = ?
            WHERE application_id = ?
            """,
            (status, interview_date, application_id),
        )
    return cursor.rowcount > 0


def delete_application(application_id: int) -> bool:
    with _connection() as connection:
        cursor = connection.execute(
            "DELETE FROM applications WHERE application_id = ?",
            (application_id,),
        )
    return cursor.rowcount > 0


def get_upcoming_interviews(today: str) -> list[dict[str, object]]:
    with _connection() as connection:
        rows = connection.execute(
            """
            SELECT application_id, company_name, job_role, interview_date
            FROM applications
            WHERE status = 'Interview Scheduled'
              AND interview_date >= ?
            ORDER BY interview_date ASC, company_name COLLATE NOCASE ASC
            """,
            (today,),
        ).fetchall()
    return [dict(row) for row in rows]


def applications_to_csv(applications: list[dict[str, object]]) -> str:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=APPLICATION_COLUMNS)
    writer.writeheader()
    writer.writerows(applications)
    return output.getvalue()


def get_total_applications() -> int:
    with _connection() as connection:
        result = connection.execute(
            "SELECT COUNT(*) FROM applications"
        ).fetchone()
    return result[0]


def get_most_applied_role() -> tuple[str, int] | None:
    with _connection() as connection:
        result = connection.execute(
            """
            SELECT job_role, COUNT(*) AS application_count
            FROM applications
            GROUP BY job_role
            ORDER BY application_count DESC, job_role COLLATE NOCASE ASC, job_role ASC
            LIMIT 1
            """
        ).fetchone()
    if result is None:
        return None
    return result[0], result[1]


def get_status_counts() -> list[dict[str, object]]:
    with _connection() as connection:
        rows = connection.execute(
            """
            SELECT status, COUNT(*) AS application_count
            FROM applications
            GROUP BY status
            ORDER BY status
            """
        ).fetchall()
    return [
        {
            "Status": row["status"] if row["status"] is not None else "Not specified",
            "Applications": row["application_count"],
        }
        for row in rows
    ]
