import sqlite3
from pathlib import Path

import streamlit as st


# Keep the database beside this Python file, even if Streamlit is started elsewhere.
DATABASE_PATH = Path(__file__).resolve().parent / "placements.db"

# These are the statuses users can choose when adding an application.
APPLICATION_STATUSES = [
    "Applied",
    "Shortlisted",
    "Interview Scheduled",
    "Selected",
    "Rejected",
]


def add_application(
    company_name: str,
    job_role: str,
    application_date: str,
    status: str,
) -> None:
    """Save one application to the database."""
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        connection.execute(
            """
            INSERT INTO applications
                (company_name, job_role, application_date, status)
            VALUES (?, ?, ?, ?)
            """,
            (company_name, job_role, application_date, status),
        )
        connection.commit()
    finally:
        connection.close()


def get_applications() -> list[dict[str, object]]:
    """Return all applications, newest application dates first."""
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            """
            SELECT application_id, company_name, job_role, application_date, status
            FROM applications
            ORDER BY application_date DESC, application_id DESC
            """
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def get_total_applications() -> int:
    """Return the number of application records."""
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        result = connection.execute(
            "SELECT COUNT(*) FROM applications"
        ).fetchone()
        return result[0]
    finally:
        connection.close()


def get_most_applied_role() -> tuple[str, int] | None:
    """Return the most applied-to role, breaking ties alphabetically."""
    connection = sqlite3.connect(DATABASE_PATH)
    try:
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
    finally:
        connection.close()


def get_status_counts() -> list[dict[str, object]]:
    """Return a count for every status found in the database."""
    connection = sqlite3.connect(DATABASE_PATH)
    try:
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
                "Status": status if status is not None else "Not specified",
                "Applications": count,
            }
            for status, count in rows
        ]
    finally:
        connection.close()


st.title("Placement Application Tracker")
st.write("Keep track of the jobs you have applied for.")

st.header("Add Application")
with st.form("add_application_form"):
    company_name = st.text_input("Company Name")
    job_role = st.text_input("Job Role")
    application_date = st.date_input("Application Date")
    status = st.selectbox("Status", APPLICATION_STATUSES)
    add_button_clicked = st.form_submit_button("Add Application")

if add_button_clicked:
    if not company_name.strip() or not job_role.strip():
        st.error("Please enter both a company name and a job role.")
    else:
        add_application(
            company_name.strip(),
            job_role.strip(),
            application_date.isoformat(),
            status,
        )
        st.success("Application added successfully.")

st.header("View Applications")
applications = get_applications()
if applications:
    st.dataframe(applications, use_container_width=True, hide_index=True)
else:
    st.info("No applications are available yet.")

st.header("Application Summary")
total_applications = get_total_applications()
st.metric("Total Applications", total_applications)

most_applied_role = get_most_applied_role()
if most_applied_role is None:
    st.write("Most Applied Role: No applications yet.")
else:
    role, role_count = most_applied_role
    st.write(f"Most Applied Role: **{role}** ({role_count} applications)")

st.subheader("Status-wise Summary")
status_counts = get_status_counts()
if status_counts:
    st.dataframe(status_counts, use_container_width=True, hide_index=True)
    st.bar_chart(status_counts, x="Status", y="Applications")
else:
    st.info("Status counts will appear here after you add an application.")
python