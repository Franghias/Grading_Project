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

# =========================
# Top Navigation Bar (moved from sidebar)
# =========================

if st.session_state.user.get('is_professor'):
    with st.sidebar:
        st.markdown("### Quick Navigation")
        st.page_link('pages/2_Professor_View.py', label='Professor View', icon='👨‍🏫')
        st.page_link('pages/5_Prompt_Management.py', label='Prompt Management', icon='📝')
        st.page_link('pages/7_Class_Statistics.py', label='Class Statistics', icon='📈')
        st.page_link('pages/6_Assignment_Management.py', label='Assignment Management', icon='🗂️')
        st.page_link('pages/create_class.py', label='Create Class', icon='➕')
        st.page_link('login.py', label='Logout', icon='🚪')
        st.markdown("---")

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

# Class selection with refresh button
col1, col2 = st.columns([3, 1])
with col1:
    selected_class = st.selectbox(
        "Select a class",
        options=classes,
        format_func=lambda x: f"{x['name']} ({x['code']})"
    )
with col2:
    if st.button("🔄 Refresh", type="secondary", help="Refresh class data and assignments"):
        st.rerun()

if selected_class:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Class Grading Prompt")
    # Fetch current class prompt
    try:
        response = requests.get(f"{API_URL}/classes/{selected_class['id']}/prompt", headers={"Authorization": f"Bearer {st.session_state.token}"})
        if response.status_code == 200:
            class_prompt = response.json()
            if class_prompt and 'prompt' in class_prompt and 'title' in class_prompt:
                st.code(class_prompt['prompt'], language="text")
                st.write(f"**Title:** {class_prompt['title']}")
            else:
                st.info("No prompt set for this class yet.")
                class_prompt = None
        else:
            st.info("No prompt set for this class yet.")
            class_prompt = None
    except Exception as e:
        st.error(f"Error fetching class prompt: {e}")

    st.markdown("---")
    st.subheader("Assign a Prompt to This Class")
    # Browse all global prompts
    try:
        response = requests.get(f"{API_URL}/prompts/", headers={"Authorization": f"Bearer {st.session_state.token}"})
        if response.status_code == 200:
            all_prompts = response.json()
            global_prompts = [p for p in all_prompts if p['class_id'] is None]
            for prompt in global_prompts:
                with st.expander(f"{prompt['title'] or 'Untitled Prompt'}"):
                    st.code(prompt['prompt'], language="text")
                    if st.button(f"Assign to this class", key=f"assign_{prompt['id']}"):
                        assign_response = requests.post(
                            f"{API_URL}/classes/{selected_class['id']}/prompt",
                            params={"prompt_id": prompt['id']},
                            headers={"Authorization": f"Bearer {st.session_state.token}"}
                        )
                        if assign_response.status_code == 200:
                            st.success("Prompt assigned to class!")
                        else:
                            st.error(f"Failed to assign prompt: {assign_response.text}")
        else:
            st.warning("Could not load prompts.")
    except Exception as e:
        st.error(f"Error loading prompts: {e}")

    st.markdown("---")
    st.subheader("Edit Class Prompt")
    st.markdown('<p>Please go to Prompt Management to edit the prompt</p>', unsafe_allow_html=True)
    # Add button to go to Prompt Management
    if st.button("Go to Prompt Management"):
        st.switch_page("pages/5_Prompt_Management.py")
else:
    st.info("No prompt to edit for this class.")


# =========================
# Grading & Feedback Section (at the end of the page)
# =========================
st.markdown("---")
st.header("📝 Grade and Give Feedback on Student Homework")
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
        assignments = []

    if not assignments:
        st.info("No assignments found for this class.")
    else:
        for assignment in assignments:
            st.markdown(f"### {assignment['name']}")
            # Fetch submissions for this assignment
            try:
                response = requests.get(
                    f"{API_URL}/classes/{selected_class['id']}/assignments/{assignment['id']}/submissions",
                    headers={"Authorization": f"Bearer {st.session_state.token}"}
                )
                response.raise_for_status()
                submissions = response.json()
            except requests.RequestException as e:
                st.error(f"Error fetching submissions: {str(e)}")
                continue
            if not submissions:
                st.info("No student submissions for this assignment yet.")
                continue
            for user_data in submissions:
                student_key = f"show_details_{assignment['id']}_{user_data['user_id']}"
                if student_key not in st.session_state:
                    st.session_state[student_key] = False
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**👨‍🎓 {user_data['username']} ({user_data['user_id']})**")
                with col2:
                    button_text = "🔽 Hide Details" if st.session_state[student_key] else "▶️ Show Details"
                    if st.button(button_text, key=f"btn_{assignment['id']}_{user_data['user_id']}"):
                        st.session_state[student_key] = not st.session_state[student_key]
                        st.rerun()
                if st.session_state[student_key]:
                    user_subs = sorted(user_data['submissions'], key=lambda x: x['created_at'], reverse=True)
                    latest_sub = user_subs[0] if user_subs else None
                    st.markdown(f"<div style='background-color: #f8fafc; padding: 1rem; border-radius: 0.5rem; border: 1px solid #e2e8f0; margin-bottom: 1rem;'>", unsafe_allow_html=True)
                    st.markdown(f"<h4 style='margin: 0 0 0.5rem 0; color: #1e293b;'>👨‍🎓 Student Information</h4>", unsafe_allow_html=True)
                    st.markdown(f"<p style='margin: 0.25rem 0; color: #475569;'><strong>Name:</strong> {user_data['username']}</p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='margin: 0.25rem 0; color: #475569;'><strong>Student ID:</strong> {user_data['user_id']}</p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='margin: 0.25rem 0; color: #475569;'><strong>Total Submissions:</strong> {len(user_subs)}</p>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                    if latest_sub:
                        left, right = st.columns(2)
                        with left:
                            st.markdown("#### 🤖 AI Grade & Feedback (Latest Submission)")
                            if latest_sub['ai_grade'] is not None:
                                st.markdown(f"**AI Grade:** {latest_sub['ai_grade']}")
                            else:
                                st.markdown("**AI Grade:** Not available")
                            if latest_sub['ai_feedback']:
                                st.markdown(f"**AI Feedback:** {latest_sub['ai_feedback']}")
                            else:
                                st.markdown("**AI Feedback:** Not available")
                            st.markdown("**Submitted Code:**")
                            st.code(latest_sub['code'], language="python")
                        with right:
                            st.markdown("#### 👨‍🏫 Professor Grade & Feedback (Edit)")
                            with st.form(f"professor_grade_form_{assignment['id']}_{latest_sub['id']}"):
                                prof_grade = st.number_input(
                                    "Grade (0-100)",
                                    min_value=0.0,
                                    max_value=100.0,
                                    step=1.0,
                                    value=float(latest_sub['professor_grade']) if latest_sub['professor_grade'] is not None else 0.0,
                                    key=f"grade_input_{assignment['id']}_{latest_sub['id']}"
                                )
                                prof_feedback = st.text_area(
                                    "Feedback (optional)",
                                    value=latest_sub['professor_feedback'] if latest_sub['professor_feedback'] else "",
                                    key=f"feedback_input_{assignment['id']}_{latest_sub['id']}",
                                    height=150
                                )
                                submit_prof_grade = st.form_submit_button("Submit Grade")
                                if submit_prof_grade:
                                    try:
                                        response = requests.post(
                                            f"{API_URL}/submissions/{latest_sub['id']}/professor-grade",
                                            headers={"Authorization": f"Bearer {st.session_state.token}"},
                                            json={"grade": prof_grade, "feedback": prof_feedback}
                                        )
                                        response.raise_for_status()
                                        result = response.json()
                                        st.success(f"Professor grade set: {result['professor_grade']} (Final Grade)")
                                        st.rerun()
                                    except requests.RequestException as e:
                                        st.error(f"Error setting professor grade: {str(e)}")
                    st.markdown("---") 