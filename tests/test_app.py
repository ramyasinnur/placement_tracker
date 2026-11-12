import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import database
from streamlit.testing.v1 import AppTest


class ApplicationUiTests(unittest.TestCase):
    def test_search_update_and_confirmed_delete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "placements.db"
            with patch.object(database, "DATABASE_PATH", database_path):
                database.initialize_database()
                database.add_application(
                    "Northwind", "Engineer", "2026-01-01", "Applied"
                )
                database.add_application(
                    "Contoso", "Analyst", "2026-01-02", "Interview Scheduled",
                    "2026-12-01",
                )

                app = AppTest.from_file(
                    str(Path(__file__).resolve().parents[1] / "app.py"),
                    default_timeout=20,
                ).run()
                self.assertEqual(len(app.exception), 0)
                self.assertEqual(len(app.get("download_button")), 1)

                app.text_input[2].set_value("north").run()
                self.assertEqual(
                    app.selectbox[2].value["company_name"], "Northwind"
                )

                app.selectbox[3].set_value("Rejected")
                app.form_submit_button[1].click().run()
                self.assertEqual(
                    database.get_applications(company_name="Northwind")[0]["status"],
                    "Rejected",
                )

                app.form_submit_button[2].click().run()
                self.assertEqual(database.get_total_applications(), 2)

                app.checkbox[0].set_value(True)
                app.form_submit_button[2].click().run()
                self.assertEqual(database.get_total_applications(), 1)
                self.assertEqual(
                    database.get_applications()[0]["company_name"], "Contoso"
                )
                self.assertEqual(len(app.exception), 0)


if __name__ == "__main__":
    unittest.main()
