import sqlite3
from pathlib import Path

import streamlit as st


DATABASE_PATH = Path(__file__).with_name("placements.db")
APPLICATION_STATUSES = [
    "Applied",
    "Shortlisted",
    "Interview Scheduled",
    "Selected",
    "Rejected",
]


def load_dashboard_data():
    """Load applications and their summary information from SQLite."""
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    try:
        applications = connection.execute(
            """
            SELECT application_id, company_name, job_role, application_date, status
            FROM applications
            ORDER BY application_id DESC
            """
        ).fetchall()
        total_applications = connection.execute(
            "SELECT COUNT(*) FROM applications"
        ).fetchone()[0]
        role_counts = connection.execute(
            """
            SELECT job_role, COUNT(*) AS application_count
            FROM applications
            WHERE job_role IS NOT NULL AND TRIM(job_role) != ''
            GROUP BY job_role
            """
        ).fetchall()
        status_counts = connection.execute(
            """
            SELECT status, COUNT(*) AS application_count
            FROM applications
            GROUP BY status
            """
        ).fetchall()
    finally:
        connection.close()

    return applications, total_applications, role_counts, status_counts


def add_application(company_name, job_role, application_date, status):
    """Save one application to the database."""
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        connection.execute(
            """
            INSERT INTO applications (company_name, job_role, application_date, status)
            VALUES (?, ?, ?, ?)
            """,
            (company_name, job_role, application_date, status),
        )
        connection.commit()
    finally:
        connection.close()


def get_most_applied_roles(role_counts):
    """Return all highest-count roles in a consistent alphabetical order."""
    if not role_counts:
        return []

    highest_count = max(row["application_count"] for row in role_counts)
    return sorted(
        (
            row["job_role"]
            for row in role_counts
            if row["application_count"] == highest_count
        ),
        key=lambda role: (role.casefold(), role),
    )


st.set_page_config(page_title="Placement Application Tracker", page_icon="📋")
st.title("Placement Application Tracker")
st.write("Keep track of your job applications and their progress.")

with st.form("add_application_form"):
    st.subheader("Add Application")
    company_name = st.text_input("Company Name")
    job_role = st.text_input("Job Role")
    application_date = st.date_input("Application Date", format="YYYY-MM-DD")
    status = st.selectbox("Status", APPLICATION_STATUSES)
    submitted = st.form_submit_button("Add Application")

if submitted:
    company_name = company_name.strip()
    job_role = job_role.strip()

    if not company_name or not job_role:
        st.error("Please enter both a company name and a job role.")
    else:
        add_application(
            company_name,
            job_role,
            application_date.isoformat(),
            status,
        )
        st.success("Application added successfully.")

st.subheader("Application Summary")

applications, total_applications, role_counts, saved_status_counts = (
    load_dashboard_data()
)
st.metric("Total Applications", total_applications)

most_applied_roles = get_most_applied_roles(role_counts)
if most_applied_roles:
    if len(most_applied_roles) == 1:
        st.write(f"Most Applied Role: **{most_applied_roles[0]}**")
    else:
        tied_roles = ", ".join(most_applied_roles)
        st.write(f"Most Applied Roles (tied, alphabetical): **{tied_roles}**")
else:
    st.write("Most Applied Role: No applications yet.")

st.subheader("Status-wise Summary")
status_totals = {status_name: 0 for status_name in APPLICATION_STATUSES}

for row in saved_status_counts:
    status_name = row["status"] or "Not specified"
    status_totals[status_name] = row["application_count"]

for status_name, count in status_totals.items():
    st.write(f"**{status_name}:** {count}")

st.bar_chart(
    {
        "Status": list(status_totals.keys()),
        "Applications": list(status_totals.values()),
    },
    x="Status",
    y="Applications",
)

st.subheader("View Applications")
if applications:
    st.dataframe(
        [dict(application) for application in applications],
        hide_index=True,
        use_container_width=True,
    )
else:
    st.info("No applications are available yet. Add one using the form above.")
