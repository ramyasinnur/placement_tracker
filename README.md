# Placement Application Tracker

A small Streamlit app for tracking job applications, interview dates, and application statuses.

Search applications by company, filter by status, update or confirm deletion of records,
and export the visible filtered results to CSV. Upcoming scheduled interviews appear
separately in date order.

## Run locally

1. Install the dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

2. Create the local SQLite database:

   ```bash
   python init_db.py
   ```

3. Start the app:

   ```bash
   streamlit run app.py
   ```

4. Run the tests:

   ```bash
   python -m unittest discover -s tests -v
   ```

The database (`placements.db`) is created locally and is intentionally not tracked by Git.
Existing databases are upgraded automatically with an optional `interview_date` column;
existing application records are preserved.
