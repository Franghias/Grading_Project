# =========================
# Professor View Page
# =========================
# This file implements the dashboard for professors to view and manage their classes, assignments, and student submissions.
# Professors can grade, provide feedback, and manage assignments from this page.

import streamlit as st
import requests
import os
from dotenv import load_dotenv
import time
from datetime import datetime

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
    page_title="Professor View",
    page_icon="👨‍🏫",
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
st.markdown('<h1>Professor View</h1>', unsafe_allow_html=True)
st.markdown('<p>View and manage class submissions</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Check if user is logged in and is a professor
if 'user' not in st.session_state:
    st.switch_page("login.py")

if not st.session_state.user.get('is_professor'):
    st.error("This page is for professors only")
    st.stop()

# Ensure custom_grading_prompt is initialized
if 'custom_grading_prompt' not in st.session_state:
    st.session_state.custom_grading_prompt = ''

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
except requests.RequestException as e:
    st.error(f"Error fetching classes: {str(e)}")
    st.stop()

if not classes:
    st.warning("You are not teaching any classes yet")
    
    # Add button to create new class
    if st.button("Create New Class", type="primary"):
        st.switch_page("pages/create_class.py")
    st.stop()

# =========================
# Class and Assignment Selection
# =========================

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
        
        # Add option to create default assignments
        if st.button("Create Default Assignments"):
            default_assignments = [
                "Hello World",
                "Print",
                "Variable Definition and How to Use It",
                "If Else Statement",
                "For Loop"
            ]
            
            for assignment_name in default_assignments:
                try:
                    response = requests.post(
                        f"{API_URL}/classes/{selected_class['id']}/assignments/",
                        headers={"Authorization": f"Bearer {st.session_state.token}"},
                        json={"name": assignment_name, "class_id": selected_class['id']}
                    )
                    response.raise_for_status()
                except requests.RequestException as e:
                    st.error(f"Error creating assignment '{assignment_name}': {str(e)}")
                    continue
            
            st.success("Default assignments created successfully!")
            st.experimental_rerun()
    else:
        # Assignment selection dropdown
        selected_assignment = st.selectbox(
            "Select an assignment",
            options=assignments,
            format_func=lambda x: x['name']
        )
        st.markdown("<div style='text-align:center; margin-top: 1rem;'>", unsafe_allow_html=True)
        if st.button("Manage Assignments"):
            st.switch_page("pages/6_Assignment_Management.py")
        st.markdown("</div>", unsafe_allow_html=True)

        if selected_assignment:
            # Fetch submissions for the selected assignment
            try:
                response = requests.get(
                    f"{API_URL}/classes/{selected_class['id']}/assignments/{selected_assignment['id']}/submissions",
                    headers={"Authorization": f"Bearer {st.session_state.token}"}
                )
                response.raise_for_status()
                submissions = response.json()
            except requests.RequestException as e:
                st.error(f"Error fetching submissions: {str(e)}")
                st.stop()

            if not submissions:
                st.info("No submissions found for this assignment")
            else:
                st.subheader(f"Submissions for {selected_assignment['name']}")
                # Grouped by user
                for user_data in submissions:
                    with st.expander(f"{user_data['username']} ({user_data['user_id']})", expanded=False):
                        user_subs = sorted(user_data['submissions'], key=lambda x: x['created_at'], reverse=True)
                        for i, submission in enumerate(user_subs, 1):
                            st.markdown(f"**Submission {i} - {submission['created_at'][:10]}**")
                            # (grade/feedback display code here, as a block)
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                if submission['ai_grade'] is not None:
                                    ai_grade_color = "green" if submission['ai_grade'] >= 70 else "orange" if submission['ai_grade'] >= 50 else "red"
                                    st.markdown(f"""
                                        <div style="background-color: #f0f9ff; padding: 1rem; border-radius: 0.5rem; text-align: center; border: 1px solid #bae6fd;">
                                            <h4 style="margin: 0 0 0.5rem 0; color: #0369a1;">🤖 AI Grade</h4>
                                            <h2 style="margin: 0; color: {ai_grade_color}; font-size: 1.5rem;">{submission['ai_grade']}</h2>
                                        </div>
                                    """, unsafe_allow_html=True)
                                else:
                                    st.markdown("**🤖 AI Grade:** Not available")
                            with col2:
                                if submission['professor_grade'] is not None:
                                    prof_grade_color = "green" if submission['professor_grade'] >= 70 else "orange" if submission['professor_grade'] >= 50 else "red"
                                    st.markdown(f"""
                                        <div style="background-color: #f0fdf4; padding: 1rem; border-radius: 0.5rem; text-align: center; border: 1px solid #bbf7d0;">
                                            <h4 style="margin: 0 0 0.5rem 0; color: #166534;">👨‍🏫 Professor Grade</h4>
                                            <h2 style="margin: 0; color: {prof_grade_color}; font-size: 1.5rem;">{submission['professor_grade']}</h2>
                                        </div>
                                    """, unsafe_allow_html=True)
                                else:
                                    st.markdown("**👨‍🏫 Professor Grade:** Not graded")
                            with col3:
                                # Only show Final Grade if professor has graded
                                if submission['professor_grade'] is not None:
                                    final_grade_color = "green" if submission['professor_grade'] >= 70 else "orange" if submission['professor_grade'] >= 50 else "red"
                                    st.markdown(f"""
                                        <div style="background-color: #fef7ff; padding: 1rem; border-radius: 0.5rem; text-align: center; border: 2px solid #c084fc;">
                                            <h4 style="margin: 0 0 0.5rem 0; color: #7c3aed;">📊 Final Grade</h4>
                                            <h2 style="margin: 0; color: {final_grade_color}; font-size: 1.5rem;">{submission['professor_grade']}</h2>
                                        </div>
                                    """, unsafe_allow_html=True)
                                # Do not show final grade if not graded by professor
                            # Feedback sections
                            col1, col2 = st.columns(2)
                            with col1:
                                if submission['ai_feedback']:
                                    st.markdown("### 🤖 AI Feedback")
                                    st.markdown(f"<div style='background-color: #f8fafc; padding: 1rem; border-radius: 0.5rem; border: 1px solid #e2e8f0;'>{submission['ai_feedback']}</div>", unsafe_allow_html=True)
                            with col2:
                                if submission['professor_feedback']:
                                    st.markdown("### 👨‍🏫 Professor Feedback")
                                    st.markdown(f"<div style='background-color: #f0fdf4; padding: 1rem; border-radius: 0.5rem; border: 1px solid #bbf7d0;'>{submission['professor_feedback']}</div>", unsafe_allow_html=True)
                            st.markdown("### Submitted Code")
                            st.code(submission['code'], language="python")
                            st.markdown("---")
                            # Add custom grading button
                            if st.button(f"Grade with Custom Prompt", key=f"custom_grade_{submission['id']}"):
                                if st.session_state.custom_grading_prompt.strip() == '':
                                    st.warning('You must set your custom grading prompt before using custom grading!')
                                else:
                                    try:
                                        response = requests.post(
                                            f"{API_URL}/submissions/grade-with-custom-prompt?submission_id={submission['id']}",
                                            headers={"Authorization": f"Bearer {st.session_state.token}"}
                                        )
                                        response.raise_for_status()
                                        result = response.json()
                                        st.success(f"Custom grade: {result['grade']}, Feedback: {result['feedback']}")
                                        st.rerun()
                                    except requests.RequestException as e:
                                        st.error(f"Error grading with custom prompt: {str(e)}")
                            # Professor grading form (only if not already graded)
                            if submission['professor_grade'] is None:
                                with st.form(f"professor_grade_form_{submission['id']}"):
                                    st.markdown("#### 👨‍🏫 Set Professor Grade (Final Score)")
                                    prof_grade = st.number_input("Grade (0-100)", min_value=0.0, max_value=100.0, step=1.0, key=f"grade_input_{submission['id']}")
                                    prof_feedback = st.text_area("Feedback (optional)", key=f"feedback_input_{submission['id']}")
                                    submit_prof_grade = st.form_submit_button("Submit Final Grade")
                                    if submit_prof_grade:
                                        try:
                                            response = requests.post(
                                                f"{API_URL}/submissions/{submission['id']}/professor-grade",
                                                headers={"Authorization": f"Bearer {st.session_state.token}"},
                                                json={"grade": prof_grade, "feedback": prof_feedback}
                                            )
                                            response.raise_for_status()
                                            result = response.json()
                                            st.success(f"Professor grade set: {result['professor_grade']} (Final Grade)")
                                            st.rerun()
                                        except requests.RequestException as e:
                                            st.error(f"Error setting professor grade: {str(e)}")

# Sidebar navigation for professors
if st.session_state.user.get('is_professor'):
    with st.sidebar:
        st.title('Professor Menu')
        st.page_link('pages/2_Professor_View.py', label='Professor View', icon='👨‍🏫')
        st.page_link('pages/5_Prompt_Management.py', label='Prompt Management', icon='📝')
        st.page_link('pages/create_class.py', label='Create Class', icon='➕')
        st.page_link('pages/4_Grades_View.py', label='Grades View', icon='📊')
        st.page_link('login.py', label='Logout', icon='🚪') 