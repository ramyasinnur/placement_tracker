# Placement Application Tracker

A small Streamlit app for tracking job applications and summarizing application statuses.

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

The database (`placements.db`) is created locally and is intentionally not tracked by Git.
