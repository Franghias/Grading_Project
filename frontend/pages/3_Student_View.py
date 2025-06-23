# =========================
# Student View Page
# =========================
# This file implements the dashboard for students to view and enroll in classes.
# Students can see their enrolled classes, available classes, and navigate to class details or grades.

import streamlit as st
import requests
import os
from dotenv import load_dotenv
import time

# =========================
# Environment and API Setup
# =========================

# Load environment variables
load_dotenv()
API_URL = os.getenv('API_URL', 'http://localhost:8000')

# =========================
# Page Configuration and Sidebar
# =========================

# Page configuration
st.set_page_config(
    page_title="Student View",
    page_icon="👨‍🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Hide default sidebar
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# =========================
# Custom CSS Styling
# =========================

st.markdown("""
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <style>
        /* Theme variables */
        :root {
            --bg-color: #f7f3e3;
            --text-color: #1a202c;
            --card-bg: #f7fafc;
            --primary-bg: #4a9a9b;
            --primary-hover: #3d8283;
            --border-color: #e2e8f0;
        }

        /* Apply theme */
        html, body, .stApp {
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* Header styling */
        .header {
            background-color: #4a9a9b;
            padding: 2rem;
            text-align: center;
            color: #ffffff;
            margin-bottom: 2rem;
        }

        /* Card styling */
        .card {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 0.375rem;
            padding: 1.5rem;
            margin-bottom: 1rem;
        }

        /* Button styling */
        .stButton > button {
            background-color: var(--primary-bg);
            color: white;
            border-radius: 0.375rem;
            padding: 0.5rem 1rem;
            font-weight: 500;
        }

        .stButton > button:hover {
            background-color: var(--primary-hover);
        }
    </style>
""", unsafe_allow_html=True)

# =========================
# Header and Access Control
# =========================

# Header
st.markdown('<div class="header">', unsafe_allow_html=True)
st.markdown('<h1>Student View</h1>', unsafe_allow_html=True)
st.markdown('<p>View and enroll in available classes</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Check if user is logged in and is a student
if 'user' not in st.session_state:
    st.switch_page("login.py")

if st.session_state.user.get('is_professor'):
    st.error("This page is for students only")
    st.stop()

# =========================
# Fetch and Organize Classes
# =========================

# Get student's classes (both enrolled and available)
try:
    response = requests.get(
        f"{API_URL}/classes/",
        headers={"Authorization": f"Bearer {st.session_state.token}"}
    )
    response.raise_for_status()
    all_classes = response.json()
except requests.RequestException as e:
    st.error(f"Error fetching classes: {str(e)}")
    st.stop()

# Initialize enrolled_classes in session state if not exists
if 'enrolled_classes' not in st.session_state:
    st.session_state.enrolled_classes = []

# Separate enrolled and available classes
enrolled_classes = []
available_classes = []

for class_data in all_classes:
    # Check if the current user is in the students list
    is_enrolled = any(student['user_id'] == st.session_state.user['user_id'] 
                     for student in class_data.get('students', []))
    
    if is_enrolled:
        enrolled_classes.append(class_data)
        # Add to session state if not already there
        if class_data['id'] not in st.session_state.enrolled_classes:
            st.session_state.enrolled_classes.append(class_data['id'])
    else:
        available_classes.append(class_data)

# =========================
# UI: Enrolled and Available Classes
# =========================

# =========================
# UI: Enrolled and Available Classes (existing code)
# =========================
col1, col2 = st.columns(2)
with col1:
    st.markdown("### Your Enrolled Classes")
    if enrolled_classes:
        for class_data in enrolled_classes:
            with st.expander(f"{class_data['name']} ({class_data['code']})", expanded=True):
                st.markdown(f"**Description:** {class_data['description'] or 'No description available'}")
                st.markdown(f"**Prerequisites:** {class_data['prerequisites'] or 'None'}")
                st.markdown(f"**Learning Objectives:** {class_data['learning_objectives'] or 'None'}")
                st.markdown("**Professors:**")
                for professor in class_data['professors']:
                    st.markdown(f"- {professor['name']} ({professor['email']})")
                # Assignment expanders
                try:
                    response = requests.get(
                        f"{API_URL}/classes/{class_data['id']}/assignments/",
                        headers={"Authorization": f"Bearer {st.session_state.token}"}
                    )
                    response.raise_for_status()
                    assignments = response.json()
                except requests.RequestException as e:
                    st.error(f"Error fetching assignments: {str(e)}")
                    assignments = []
                if assignments:
                    for assignment in assignments:
                        with st.expander(f"Assignment: {assignment['name']}", expanded=False):
                            st.markdown(f"**Description:** {assignment.get('description', 'No description')}")
                            # Fetch student's submissions for this assignment
                            try:
                                response = requests.get(
                                    f"{API_URL}/submissions/",
                                    headers={"Authorization": f"Bearer {st.session_state.token}"}
                                )
                                response.raise_for_status()
                                all_submissions = response.json()
                            except requests.RequestException as e:
                                st.error(f"Error fetching submissions: {str(e)}")
                                all_submissions = []
                            my_subs = [s for s in all_submissions if s['assignment_id'] == assignment['id'] and s['class_id'] == class_data['id']]

                            # Fetch class prompt for this class
                            try:
                                prompt_response = requests.get(
                                    f"{API_URL}/classes/{class_data['id']}/prompt",
                                    headers={"Authorization": f"Bearer {st.session_state.token}"}
                                )
                                if prompt_response.status_code == 200:
                                    class_prompt = prompt_response.json().get('prompt', '')
                                else:
                                    class_prompt = ''
                            except Exception as e:
                                class_prompt = ''

                            if not class_prompt:
                                st.warning("Waiting for professor to add AI grading prompt for this class.")
                                st.info("You can still submit your code, but AI grading will be available once your professor adds a prompt.")
                                with st.form(key=f"submit_form_{class_data['id']}_{assignment['id']}"):
                                    code = st.text_area("Paste your code here:", height=200)
                                    submit_btn = st.form_submit_button("Submit Code")
                                    if submit_btn:
                                        if not code.strip():
                                            st.error("Please enter your code before submitting.")
                                        else:
                                            try:
                                                submit_response = requests.post(
                                                    f"{API_URL}/submissions/",
                                                    data={
                                                        "code": code,
                                                        "class_id": class_data['id'],
                                                        "assignment_id": assignment['id']
                                                    },
                                                    headers={"Authorization": f"Bearer {st.session_state.token}"}
                                                )
                                                submit_response.raise_for_status()
                                                st.success("Code submitted successfully! AI grading will be available once your professor adds a prompt.")
                                                st.experimental_rerun()
                                            except requests.RequestException as e:
                                                st.error(f"Error submitting code: {str(e)}")
                                # Show previous submissions (without AI grading)
                                if my_subs:
                                    for i, sub in enumerate(sorted(my_subs, key=lambda x: x['created_at']), 1):
                                        st.markdown(f"**Submission {i}**")
                                        st.markdown(f"- **Submitted at:** {sub.get('created_at', '')[:19].replace('T', ' ')}")
                                        st.markdown("**Submitted Code:**")
                                        st.code(sub.get('code', ''), language="python")
                                        st.markdown("---")
                                else:
                                    st.info("No submissions for this assignment yet.")
                            else:
                                st.success("AI grading is enabled for this class.")
                                with st.form(key=f"submit_form_{class_data['id']}_{assignment['id']}"):
                                    code = st.text_area("Paste your code here:", height=200)
                                    submit_btn = st.form_submit_button("Submit Code")
                                    if submit_btn:
                                        if not code.strip():
                                            st.error("Please enter your code before submitting.")
                                        else:
                                            try:
                                                submit_response = requests.post(
                                                    f"{API_URL}/submissions/",
                                                    data={
                                                        "code": code,
                                                        "class_id": class_data['id'],
                                                        "assignment_id": assignment['id']
                                                    },
                                                    headers={"Authorization": f"Bearer {st.session_state.token}"}
                                                )
                                                submit_response.raise_for_status()
                                                st.success("Code submitted successfully! Check below for your AI grade and feedback.")
                                                st.experimental_rerun()
                                            except requests.RequestException as e:
                                                st.error(f"Error submitting code: {str(e)}")
                                # Show previous submissions (with AI grading/results)
                                if my_subs:
                                    for i, sub in enumerate(sorted(my_subs, key=lambda x: x['created_at']), 1):
                                        st.markdown(f"**Submission {i}**")
                                        st.markdown(f"- **Final Grade:** {sub.get('final_grade', 'N/A')}")
                                        st.markdown(f"- **Professor Feedback:** {sub.get('professor_feedback', 'N/A')}")
                                        st.markdown(f"- **AI Grade:** {sub.get('ai_grade', 'N/A')}")
                                        st.markdown(f"- **AI Feedback:** {sub.get('ai_feedback', 'N/A')}")
                                        st.markdown(f"- **Submitted at:** {sub.get('created_at', '')[:19].replace('T', ' ')}")
                                        st.markdown("**Submitted Code:**")
                                        st.code(sub.get('code', ''), language="python")
                                        st.markdown("---")
                                else:
                                    st.info("No submissions for this assignment yet.")
                else:
                    st.info("No assignments for this class.")
                # Button to view class details
                if st.button(f"Go to {class_data['name']}", key=f"view_{class_data['id']}"):
                    st.session_state.selected_class = class_data
                    st.switch_page("pages/1_Home.py")
    else:
        st.info("You haven't enrolled in any classes yet.")
with col2:
    st.markdown("### Available Classes")
    if available_classes:
        for class_data in available_classes:
            with st.expander(f"{class_data['name']} ({class_data['code']})", expanded=True):
                st.markdown(f"**Description:** {class_data['description'] or 'No description available'}")
                st.markdown(f"**Prerequisites:** {class_data['prerequisites'] or 'None'}")
                st.markdown(f"**Learning Objectives:** {class_data['learning_objectives'] or 'None'}")
                st.markdown("**Professors:**")
                for professor in class_data['professors']:
                    st.markdown(f"- {professor['name']} ({professor['email']})")
                # Enroll button
                if st.button(f"Enroll in {class_data['name']}", key=f"enroll_{class_data['id']}"):
                    try:
                        response = requests.post(
                            f"{API_URL}/classes/{class_data['id']}/enroll",
                            headers={"Authorization": f"Bearer {st.session_state.token}"}
                        )
                        response.raise_for_status()
                        st.success(f"Successfully enrolled in {class_data['name']}!")
                        st.session_state.enrolled_classes.append(class_data['id'])
                        st.session_state.selected_class = class_data
                        time.sleep(2)
                        st.switch_page("pages/1_Home.py")
                    except requests.RequestException as e:
                        st.error(f"Error enrolling in class: {str(e)}")
    else:
        st.info("No available classes to enroll in at the moment.")
st.markdown("---")

# =========================
# Navigation and Logout Buttons
# =========================

# Navigation and logout buttons at the bottom
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Refresh Page"):
        st.rerun()
with col2:
    if st.button("View All Grades"):
        st.switch_page("pages/4_Grades_View.py")
with col3:
    if st.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("login.py")

# =========================
# Sidebar Navigation
# =========================

# Sidebar navigation for students
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