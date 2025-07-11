# =========================
# Submit Assignment Page
# =========================
# This file implements the submission page for students to submit code for assignments.
# Students can select a class and assignment, enter or upload code, and submit for AI grading.

import streamlit as st
import requests
import os
from dotenv import load_dotenv
import time

# =========================
# Environment and API Setup
# =========================

from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / '.env'

# Load environment variables from .env file
load_dotenv(dotenv_path=env_path)

API_URL = os.getenv('API_URL', 'http://localhost:8000').strip()

# =========================
# Page Configuration and Sidebar
# =========================

# Page configuration
st.set_page_config(
    page_title="Submit Assignment",
    page_icon="📝",
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
            --input-bg: #ffffff;
            --input-border: #cbd5e0;
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
st.markdown('<h1>Submit Assignment</h1>', unsafe_allow_html=True)
st.markdown('<p>Submit your code for grading</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Check if user is logged in
if 'user' not in st.session_state:
    st.switch_page("login.py")

# =========================
# Fetch Classes and Assignments
# =========================

# Get user's enrolled classes
try:
    response = requests.get(
        f"{API_URL}/classes/",
        headers={"Authorization": f"Bearer {st.session_state.token}"}
    )
    response.raise_for_status()
    classes = response.json()
except requests.RequestException as e:
    st.error(f"Error fetching classes: {str(e)}")
    st.stop()

if not classes:
    st.warning("You are not enrolled in any classes")
    st.stop()

# Class selection dropdown
selected_class = st.selectbox(
    "Select a class",
    options=classes,
    format_func=lambda x: f"{x['name']} ({x['code']})"
)

if selected_class:
    # Fetch assignments for the selected class
    try:
        response = requests.get(
            f"{API_URL}/classes/{selected_class['id']}/assignments/",
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        response.raise_for_status()
        assignments = response.json()
    except requests.RequestException as e:
        st.error(f"Error fetching assignments: {str(e)}")
        st.stop()

    if not assignments:
        st.warning("No assignments found for this class")
    else:
        # Assignment selection dropdown
        selected_assignment = st.selectbox(
            "Select an assignment",
            options=assignments,
            format_func=lambda x: x['name']
        )

        if selected_assignment:
            # -------------------------
            # Submission Form
            # -------------------------
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown(f"### {selected_assignment['name']}")
            if selected_assignment.get('description'):
                st.markdown(selected_assignment['description'])
            st.info('The AI will grade your code using the assignment description above as context.')
            
            # Code input
            code = st.text_area(
                "Enter your code",
                height=300,
                help="Write your Python code here"
            )
            
            # File upload
            uploaded_file = st.file_uploader(
                "Or upload a Python file",
                type=['py'],
                help="Upload a .py file instead of writing code directly"
            )
            
            # Submit button
            if st.button("Submit"):
                if not code and not uploaded_file:
                    st.error("Please either enter code or upload a file")
                else:
                    try:
                        # Prepare form data
                        files = {}
                        data = {
                            "class_id": str(selected_class['id']),
                            "assignment_id": str(selected_assignment['id'])
                        }
                        
                        if uploaded_file:
                            files['file'] = uploaded_file
                        else:
                            data['code'] = code
                        
                        # Submit code
                        response = requests.post(
                            f"{API_URL}/submissions/",
                            headers={"Authorization": f"Bearer {st.session_state.token}"},
                            data=data,
                            files=files
                        )
                        response.raise_for_status()
                        
                        st.success("Submission successful!")
                        time.sleep(2)
                        st.rerun()
                    except requests.RequestException as e:
                        st.error(f"Error submitting code: {str(e)}")
            
            st.markdown('</div>', unsafe_allow_html=True)

# =========================
# Sidebar Navigation
# =========================

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