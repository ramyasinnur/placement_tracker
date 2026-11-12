from datetime import date

import streamlit as st

from database import (
    APPLICATION_STATUSES,
    add_application,
    applications_to_csv,
    delete_application,
    get_applications,
    get_most_applied_role,
    get_status_counts,
    get_statuses,
    get_total_applications,
    get_upcoming_interviews,
    initialize_database,
    update_application,
)


def _display_application(application: dict[str, object]) -> str:
    return (
        f"{application['company_name']} — {application['job_role']} "
        f"(#{application['application_id']})"
    )


def _date_or_none(value: object) -> date | None:
    if not value:
        return None
    return date.fromisoformat(str(value))


initialize_database()

st.title("Placement Application Tracker")
st.write("Keep track of the jobs you have applied for.")
success_notice = st.session_state.pop("success_notice", None)
if success_notice:
    st.success(success_notice)

st.header("Add Application")
with st.form("add_application_form"):
    company_name = st.text_input("Company Name")
    job_role = st.text_input("Job Role")
    application_date = st.date_input("Application Date")
    status = st.selectbox("Status", APPLICATION_STATUSES)
    interview_date = st.date_input("Interview Date (optional)", value=None)
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
            interview_date.isoformat() if interview_date else None,
        )
        st.session_state["success_notice"] = "Application added successfully."
        st.rerun()

st.header("Upcoming Interviews")
upcoming_interviews = get_upcoming_interviews(date.today().isoformat())
if upcoming_interviews:
    st.dataframe(upcoming_interviews, width="stretch", hide_index=True)
else:
    st.info("No upcoming interviews are scheduled.")

st.header("View Applications")
search_company = st.text_input("Search by company name")
available_statuses = ["All statuses", *get_statuses()]
selected_status = st.selectbox("Filter by status", available_statuses)
applications = get_applications(
    company_name=search_company,
    status=None if selected_status == "All statuses" else selected_status,
)

if applications:
    st.dataframe(applications, width="stretch", hide_index=True)
    st.download_button(
        "Export filtered applications as CSV",
        data=applications_to_csv(applications),
        file_name="placement_applications.csv",
        mime="text/csv",
    )

    st.subheader("Update or Delete an Application")
    selected_application = st.selectbox(
        "Choose an application",
        applications,
        format_func=_display_application,
        key="manage_application",
    )
    application_statuses = list(APPLICATION_STATUSES)
    current_status = selected_application["status"]
    if current_status and current_status not in application_statuses:
        application_statuses.append(str(current_status))

    with st.form("update_application_form"):
        updated_status = st.selectbox(
            "Application status",
            application_statuses,
            index=application_statuses.index(current_status)
            if current_status in application_statuses
            else 0,
        )
        updated_interview_date = st.date_input(
            "Interview Date",
            value=_date_or_none(selected_application["interview_date"]),
        )
        update_clicked = st.form_submit_button("Save Changes")

    if update_clicked:
        updated = update_application(
            int(selected_application["application_id"]),
            updated_status,
            updated_interview_date.isoformat() if updated_interview_date else None,
        )
        if updated:
            st.session_state["success_notice"] = "Application updated."
            st.rerun()
        else:
            st.error("The selected application no longer exists.")

    with st.form("delete_application_form"):
        confirm_delete = st.checkbox(
            f"I confirm I want to delete {_display_application(selected_application)}"
        )
        delete_clicked = st.form_submit_button("Delete Application")

    if delete_clicked:
        if not confirm_delete:
            st.error("Confirm deletion before deleting this application.")
        elif delete_application(int(selected_application["application_id"])):
            st.session_state["success_notice"] = "Application deleted."
            st.rerun()
        else:
            st.error("The selected application no longer exists.")
else:
    if search_company or selected_status != "All statuses":
        st.info("No applications match these filters.")
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
    st.dataframe(status_counts, width="stretch", hide_index=True)
    st.bar_chart(status_counts, x="Status", y="Applications")
else:
    st.info("Status counts will appear here after you add an application.")
