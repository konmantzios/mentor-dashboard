import os
import streamlit as st
from pyairtable import Api

st.set_page_config(page_title='Mentor Portal', page_icon='🎓', layout='wide', initial_sidebar_state='expanded')

# This starter demonstrates a single-user/private dashboard. Add OIDC login and
# server-side access checks before granting access to multiple mentors.
@st.cache_resource
def airtable_api():
    return Api(st.secrets['AIRTABLE_TOKEN'])

@st.cache_data(ttl=120, show_spinner=False)
def fetch_records(table_name):
    return airtable_api().table(st.secrets['AIRTABLE_BASE_ID'], table_name).all()

def fields(record):
    return record.get('fields', {})

def linked_to_student(record, student_id):
    f = fields(record)
    value = f.get('Student', [])
    return student_id in value if isinstance(value, list) else value == student_id

def get_related(table, student_id):
    return [r for r in fetch_records(table) if linked_to_student(r, student_id)]

def val(data, key, default='—'):
    value = data.get(key)
    if value is None or value == '' or value == []:
        return default
    return ', '.join(str(v) for v in value) if isinstance(value, list) else str(value)

def attachment_links(data):
    for item in data.get('Attachment', []) or []:
        if isinstance(item, dict) and item.get('url'):
            st.link_button(item.get('filename', 'View attachment'), item['url'])

st.markdown('''<style>
[data-testid="stSidebar"] {background: #191a30;}
[data-testid="stSidebar"] * {color: #f5f5fa;}
.block-container {padding-top: 2rem; max-width: 1550px;}
.student-card {border:1px solid #e9edf2; border-left:3px solid #ed2452;
 border-radius:10px; padding:16px 20px; background:white; margin-bottom:8px;}
.muted {color:#78869b;font-size:0.85rem;}
</style>''', unsafe_allow_html=True)

with st.sidebar:
    st.title('Mentor Portal')
    st.caption('Private dashboard starter')
    section = st.radio('Navigation', ['Confirmed Students', 'Prospective Students', 'Resources'])
    if st.button('Refresh Data', use_container_width=True):
        fetch_records.clear()
        st.rerun()

if section == 'Resources':
    st.title('Resources')
    st.info('Add your mentor documents and resource links here.')
    st.stop()

try:
    students = fetch_records('Students')
except Exception as exc:
    st.error('Could not load Airtable. Check the base ID, token permissions, and table names.')
    st.exception(exc)
    st.stop()

# Demo only: never rely on this UI filter as a multi-user authorization boundary.
status_filter = 'Confirmed' if section == 'Confirmed Students' else 'Prospective'
students = [r for r in students if fields(r).get('Status') == status_filter]

if 'selected_student' not in st.session_state:
    st.session_state.selected_student = None

if st.session_state.selected_student not in {r['id'] for r in students}:
    st.session_state.selected_student = None

if st.session_state.selected_student is None:
    st.title(section)
    st.caption('Choose a student to review their background, meetings, submissions, and payments.')
    query = st.text_input('Search by student name', placeholder='Search...')
    program_options = sorted({str(fields(r).get('Program', 'Not specified')) for r in students})
    program = st.selectbox('Program', ['All programs'] + program_options)
    shown = [r for r in students if query.lower() in str(fields(r).get('Student Name', '')).lower()
             and (program == 'All programs' or str(fields(r).get('Program', 'Not specified')) == program)]
    st.caption(f'{len(shown)} students')
    for record in shown:
        d = fields(record)
        left, right = st.columns([5, 1])
        with left:
            st.markdown(f'**{val(d, "Student Name")} | {val(d, "Cohort")} | {val(d, "Program")}**')
            st.caption(f'Preferred name: {val(d, "Preferred Name")}  ·  Status: {val(d, "Status")}  ·  Location: {val(d, "Location")}')
        with right:
            if st.button('View →', key=record['id'], use_container_width=True):
                st.session_state.selected_student = record['id']
                st.rerun()
        st.divider()
else:
    student = next(r for r in students if r['id'] == st.session_state.selected_student)
    d = fields(student)
    if st.button('← Back to Student List'):
        st.session_state.selected_student = None
        st.rerun()
    st.title(f'{val(d, "Student Name")} | {val(d, "Cohort")} | {val(d, "Program")}')
    tabs = st.tabs(['Student Background', 'Meeting Summary', 'Student Deadlines & Submissions', 'Your Submissions', 'Payment Information'])
    with tabs[0]:
        st.subheader('Student Overview')
        a,b,c = st.columns(3)
        a.metric('Preferred name', val(d, 'Preferred Name'))
        b.metric('Location', val(d, 'Location'))
        c.metric('Status', val(d, 'Status'))
        st.subheader('Program Details')
        st.write('Research area:', val(d, 'Research Area'))
        st.write('Graduation year:', val(d, 'Graduation Year'))
        st.subheader('Background & Notes')
        st.write(val(d, 'Background'))
    with tabs[1]:
        meetings = sorted(get_related('Meetings', student['id']), key=lambda r: str(fields(r).get('Meeting Date', '')), reverse=True)
        st.subheader('Meeting Summary')
        required = int(d.get('Required Meetings', 0) or 0)
        completed = sum(fields(r).get('Attendance') == 'Completed' for r in meetings)
        a,b,c = st.columns(3)
        a.metric('Completed meetings', completed)
        b.metric('Required meetings', required)
        c.metric('No-shows', sum(fields(r).get('Attendance') == 'No Show' for r in meetings))
        if required:
            st.progress(min(completed/required,1.0))
        st.subheader('Meeting Notes')
        for r in meetings:
            f=fields(r)
            with st.expander(f'{val(f,"Meeting Date")} · {val(f,"Attendance")}'):
                st.write('Duration (minutes):', val(f,'Duration'))
                st.write(val(f,'Notes'))
    with tabs[2]:
        st.subheader('Student Deadlines & Submissions')
        for r in get_related('Student Submissions', student['id']):
            f=fields(r)
            st.write(f'**{val(f,"Task")}** · Due: {val(f,"Due Date")} · Status: {val(f,"Status")}')
            st.caption('Submitted: '+val(f,'Submitted Date'))
            attachment_links(f)
            st.divider()
    with tabs[3]:
        st.subheader('Mentor Submissions')
        for r in get_related('Mentor Submissions', student['id']):
            f=fields(r)
            st.write(f'**{val(f,"Document Type")}** · Due: {val(f,"Due Date")} · Submitted: {val(f,"Submitted Date")}')
            attachment_links(f)
            st.divider()
    with tabs[4]:
        st.subheader('Payment Information')
        payments=get_related('Payments', student['id'])
        if not payments:
            st.info('No payment records found.')
        for r in payments:
            f=fields(r)
            a,b,c,dcol=st.columns(4)
            a.metric('Hours',val(f,'Hours'))
            b.metric('Rate',val(f,'Rate'))
            c.metric('Amount',val(f,'Amount'))
            dcol.metric('Status',val(f,'Status'))
            st.caption('Payment date: '+val(f,'Payment Date'))
            st.divider()
