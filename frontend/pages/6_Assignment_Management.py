# =========================
# Assignment Management Page
# =========================
# This file implements the assignment management interface for professors.
# Professors can create, view, and edit assignments for their classes.
# Includes forms for creating and editing assignments, and API calls for data management.

import streamlit as st
import requests
import os
from dotenv import load_dotenv

# =========================
# Environment and API Setup
# =========================

# Load environment variables
load_dotenv()
API_URL = os.getenv("API_URL", "http://localhost:8000")

# =========================
# Page Configuration and Sidebar
# =========================

st.set_page_config(
    page_title="Assignment Management",
    page_icon="✍️",
    layout="wide"
)

# Custom CSS for styling
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# =========================
# Sidebar Navigation
# =========================

if 'user' not in st.session_state:
    st.switch_page("login.py")

if 'user' in st.session_state:
    if st.session_state.user.get('is_professor'):
        with st.sidebar:
            st.title('Professor Menu')
            st.page_link('pages/2_Professor_View.py', label='Professor View', icon='👨‍🏫')
            st.page_link('pages/5_Prompt_Management.py', label='Prompt Management', icon='📝')
            st.page_link('pages/create_class.py', label='Create Class', icon='➕')
            st.page_link('pages/4_Grades_View.py', label='Grades View', icon='📊')
            st.page_link('pages/6_Assignment_Management.py', label='Assignment Management', icon='🗂️')
            st.page_link('login.py', label='Logout', icon='🚪')
    else:
        with st.sidebar:
            st.title('Student Menu')
            st.page_link('pages/3_Student_View.py', label='Student View', icon='👨‍🎓')
            st.page_link('pages/1_Home.py', label='Home', icon='🏠')
            st.page_link('pages/4_Grades_View.py', label='Grades View', icon='📊')
            st.page_link('login.py', label='Logout', icon='🚪')

# =========================
# Header and Access Control
# =========================

# Header
st.title("Assignment Management")
st.write("Create, view, and edit assignments for your classes.")

# Check if user is logged in and is a professor
if 'user' not in st.session_state or not st.session_state.user.get('is_professor'):
    st.error("You must be logged in as a professor to access this page.")
    st.stop()

# =========================
# Fetch Professor's Classes
# =========================

try:
    response = requests.get(
        f"{API_URL}/classes/",
        headers={"Authorization": f"Bearer {st.session_state.token}"}
    )
    response.raise_for_status()
    classes = response.json()
    if not classes:
        st.warning("You are not teaching any classes. Please create a class first.")
        st.stop()
except requests.RequestException as e:
    st.error(f"Error fetching classes: {e}")
    st.stop()

# =========================
# Class Selection Dropdown
# =========================

class_options = {c['id']: f"{c['name']} ({c['code']})" for c in classes}
selected_class_id = st.selectbox("Select a Class", options=list(class_options.keys()), format_func=lambda x: class_options[x])

st.markdown("---")

# =========================
# Create New Assignment Form
# =========================

st.header("Create New Assignment")
with st.form("new_assignment_form", clear_on_submit=True):
    assignment_name = st.text_input("Assignment Name")
    assignment_description = st.text_area("Assignment Description")
    submitted = st.form_submit_button("Create Assignment")

    if submitted:
        if not assignment_name:
            st.error("Assignment name is required.")
        else:
            try:
                response = requests.post(
                    f"{API_URL}/classes/{selected_class_id}/assignments/",
                    headers={"Authorization": f"Bearer {st.session_state.token}"},
                    json={"name": assignment_name, "description": assignment_description, "class_id": selected_class_id}
                )
                response.raise_for_status()
                st.success("Assignment created successfully!")
            except requests.RequestException as e:
                st.error(f"Error creating assignment: {e}")

st.markdown("---")

# =========================
# Edit Existing Assignment
# =========================

st.header("Edit Existing Assignment")

# Fetch assignments for the selected class
if selected_class_id:
    try:
        response = requests.get(
            f"{API_URL}/classes/{selected_class_id}/assignments/",
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        response.raise_for_status()
        assignments = response.json()

        if not assignments:
            st.info("No assignments found for this class.")
        else:
            assignment_options = {a['id']: a['name'] for a in assignments}
            selected_assignment_id = st.selectbox(
                "Select an Assignment to Edit",
                options=list(assignment_options.keys()),
                format_func=lambda x: assignment_options[x]
            )

            if selected_assignment_id:
                # Get the selected assignment details
                selected_assignment = next((a for a in assignments if a['id'] == selected_assignment_id), None)

                with st.form("edit_assignment_form"):
                    edit_assignment_name = st.text_input("Assignment Name", value=selected_assignment['name'])
                    edit_assignment_description = st.text_area("Assignment Description", value=selected_assignment.get('description', ''))
                    update_submitted = st.form_submit_button("Update Assignment")

                    if update_submitted:
                        if not edit_assignment_name:
                            st.error("Assignment name is required.")
                        else:
                            try:
                                # This endpoint does not exist yet. I will create it in the backend.
                                response = requests.put(
                                    f"{API_URL}/assignments/{selected_assignment_id}",
                                    headers={"Authorization": f"Bearer {st.session_state.token}"},
                                    json={"name": edit_assignment_name, "description": edit_assignment_description}
                                )
                                response.raise_for_status()
                                st.success("Assignment updated successfully!")
                                st.rerun()
                            except requests.RequestException as e:
                                st.error(f"Error updating assignment: {e}")

    except requests.RequestException as e:
        st.error(f"Error fetching assignments: {e}") 