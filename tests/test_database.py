import csv
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import database


class DatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "placements.db"
        self.database_override = patch.object(
            database, "DATABASE_PATH", self.database_path
        )
        self.database_override.start()
        database.initialize_database()

    def tearDown(self) -> None:
        self.database_override.stop()
        self.temp_dir.cleanup()

    def test_migration_preserves_existing_applications(self) -> None:
        connection = sqlite3.connect(self.database_path)
        try:
            connection.execute("DROP TABLE applications")
            connection.execute(
                """
                CREATE TABLE applications (
                    application_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT NOT NULL,
                    job_role TEXT NOT NULL,
                    application_date TEXT,
                    status TEXT
                )
                """
            )
            connection.execute(
                """
                INSERT INTO applications
                    (company_name, job_role, application_date, status)
                VALUES ('Northwind', 'Engineer', '2026-01-01', 'Applied')
                """
            )
            connection.commit()
        finally:
            connection.close()

        database.initialize_database()
        application = database.get_applications()[0]

        self.assertEqual(application["company_name"], "Northwind")
        self.assertIsNone(application["interview_date"])

    def test_search_filter_and_csv_export(self) -> None:
        database.add_application(
            "Northwind", "Engineer", "2026-01-01", "Applied"
        )
        database.add_application(
            "Contoso", "Analyst", "2026-01-02", "Interview Scheduled"
        )

        results = database.get_applications(company_name="wind", status="Applied")
        exported = list(csv.DictReader(database.applications_to_csv(results).splitlines()))

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["company_name"], "Northwind")
        self.assertEqual(exported[0]["company_name"], "Northwind")
        self.assertIn("interview_date", exported[0])

    def test_status_and_interview_date_update(self) -> None:
        database.add_application(
            "Northwind", "Engineer", "2026-01-01", "Applied"
        )
        application_id = int(database.get_applications()[0]["application_id"])

        self.assertTrue(
            database.update_application(
                application_id, "Interview Scheduled", "2026-12-01"
            )
        )
        self.assertEqual(
            database.get_upcoming_interviews("2026-11-30")[0]["interview_date"],
            "2026-12-01",
        )
        self.assertEqual(database.get_upcoming_interviews("2026-12-02"), [])

    def test_delete_requires_existing_record(self) -> None:
        database.add_application("Northwind", "Engineer", "2026-01-01", "Applied")
        application_id = int(database.get_applications()[0]["application_id"])

        self.assertTrue(database.delete_application(application_id))
        self.assertFalse(database.delete_application(application_id))
        self.assertEqual(database.get_total_applications(), 0)

    def test_update_rejects_unsupported_status(self) -> None:
        with self.assertRaises(ValueError):
            database.update_application(1, "Unknown", None)


if __name__ == "__main__":
    unittest.main()
