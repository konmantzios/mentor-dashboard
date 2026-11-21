# Streamlit + Airtable Mentor Dashboard (starter)

This is an illustrative PRIVATE / SINGLE-USER read-only dashboard. It does **not** implement mentor authentication or row-level authorization. Do not expose real student or payment data to other users until those controls are added.

## Start
1. Set up the six Airtable tables described below, including exactly these field names.
2. Create an Airtable personal access token with `data.records:read` scope for the specific base.
3. `pip install -r requirements.txt`
4. Copy `.streamlit/secrets.example.toml` to `.streamlit/secrets.toml`, then fill in the token and base ID.
5. `streamlit run app.py`

Never commit `.streamlit/secrets.toml` to a repository.

## Schema

- **Students**: Student Name, Preferred Name, Cohort, Program, Status (Confirmed or Prospective), Location, Research Area, Graduation Year, Background (long text), Required Meetings (number).
- **Meetings**: Student (linked to Students), Meeting Date, Duration (minutes), Attendance (Completed/No Show/etc.), Notes.
- **Student Submissions**: Student (linked), Task, Due Date, Submitted Date, Status, Attachment.
- **Mentor Submissions**: Student (linked), Document Type, Due Date, Submitted Date, Attachment.
- **Payments**: Student (linked), Hours, Rate, Amount, Status, Payment Date.
- **Mentors**: Name, Email, Role, Hourly Rate, Active. (Recommended future connection via Student's Mentor linked field.)

## Important limitations
- Private single-user proof of concept only. UI filtering is not an authorization mechanism.
- No login, no per-mentor filter, no write-back.
- Airtable field names must match, otherwise fields appear as blanks.
- Dates are shown as raw strings and not yet formatted.
- Attachment URLs supplied by Airtable can expire; fetch fresh links when needed.
- Use an authenticated identity provider (e.g., OIDC), a trusted mapping of identity to Mentor record, and **server-side authorization of student/meeting/payment records** before real multi-user release.
- Restrict access to payment info by role, and follow the applicable privacy and safeguarding rules for student information.
