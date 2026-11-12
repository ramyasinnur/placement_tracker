import sqlite3

# Connect to the SQLite database. SQLite creates the file if it does not exist.
connection = sqlite3.connect("placements.db")
cursor = connection.cursor()

# Create the applications table only if it does not already exist.
cursor.execute("""
    CREATE TABLE IF NOT EXISTS applications (
        application_id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT NOT NULL,
        job_role TEXT NOT NULL,
        application_date TEXT,
        status TEXT
    )
""")

# Save the table creation and close the database connection.
connection.commit()
connection.close()

# Let the user know the database and table are ready.
print("Database and applications table created successfully.")
