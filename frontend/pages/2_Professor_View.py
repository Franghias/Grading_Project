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
import json

# =========================
# Environment and API Setup
# =========================
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
API_URL = os.getenv('API_URL', 'http://localhost:8000').strip()

# =========================
# Page Configuration and Sidebar
# =========================
st.set_page_config(
    page_title="Professor View",
    page_icon="👨‍🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# Custom CSS Styling (Consistent with new theme)
# =========================
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        [data-testid="stSidebarNav"] {display: none;}
        :root {
            /* New Earthy Palette */
            --primary-color: #d4a373;         /* Tan (for headings and primary actions) */
            --primary-hover-color: #faedcd;    /* Sandy Beige (for button hover) */
            --background-color: #e9edc9;      /* Pale Green/Yellow (main background) */
            --card-background-color: #fefae0; /* Creamy Yellow (card background) */
            --text-color: #5d4037;            /* Dark Brown for main text */
            --subtle-text-color: #8a817c;      /* Muted gray-brown for paragraphs */
            --border-color: #ccd5ae;          /* Muted Earthy Green (borders) */
        }
        .stApp {
            background-color: var(--background-color);
            font-family: 'Inter', sans-serif;
            color: var(--text-color);
        }
        .main .block-container {
            padding: 2rem;
            animation: fadeIn 0.5s ease-in-out forwards;
        }
        .header {
            background-color: var(--card-background-color);
            padding: 2rem;
            text-align: center;
            color: var(--text-color);
            margin-bottom: 2rem;
            border-radius: 12px;
            border: 1px solid var(--border-color);
        }
        .header h1 { font-size: 2.5rem; font-weight: 700; color: var(--text-color); }
        .styled-card, .stExpander {
            background-color: var(--card-background-color);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 12px rgba(212, 163, 115, 0.05);
            margin-bottom: 1.5rem;
        }
        .stExpander header { 
            font-size: 1.25rem; 
            font-weight: 600;
            color: var(--text-color);
        }
        .stButton > button {
            border-radius: 8px;
            padding: 0.6rem 1.2rem;
            font-weight: 600;
            transition: all 0.2s ease-in-out;
            background-color: var(--primary-color);
            color: var(--text-color);
            border: 1px solid var(--primary-color);
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            background-color: var(--primary-hover-color);
            border-color: var(--primary-hover-color);
            box-shadow: 0 4px 12px rgba(212, 163, 115, 0.15);
        }
        .stButton > button[kind="secondary"] { 
            background-color: transparent;
            color: var(--primary-color);
        }
        .stButton > button[kind="secondary"]:hover { 
             background-color: var(--primary-hover-color);
             color: var(--text-color);
             border-color: var(--primary-hover-color);
        }
        .info-box {
            background-color: var(--background-color);
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid var(--border-color);
            margin-bottom: 1rem;
        }
    </style>
""", unsafe_allow_html=True)


# =========================
# Header and Access Control
# =========================
st.markdown('<div class="header"><h1>Professor View</h1><p>View and manage class submissions</p></div>', unsafe_allow_html=True)

if 'user' not in st.session_state or not st.session_state.user.get('is_professor'):
    st.error("This page is for professors only.")
    st.switch_page("login.py")
    st.stop()

# =========================
# Sidebar Navigation
# =========================
with st.sidebar:
    st.title("👨‍🏫 Professor Menu")
    st.page_link('pages/2_Professor_View.py', label='Professor View', icon='📝')
    st.page_link('pages/5_Prompt_Management.py', label='Prompt Management', icon='🧠')
    st.page_link('pages/6_Assignment_Management.py', label='Assignment Management', icon='🗂️')
    st.page_link('pages/create_class.py', label='Create a New Class', icon='➕')
    st.page_link('pages/7_Class_Statistics.py', label='Class Statistics', icon='📊')
    st.markdown("---")
    if st.button("Logout", use_container_width=True, type="secondary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("login.py")


# =========================
# Caching for Performance Optimization
# =========================
@st.cache_data(ttl=10)  # Reduced from 300 to 10 seconds for faster updates
def fetch_assignments_cached(class_id, token):
    try:
        response = requests.get(f"{API_URL}/classes/{class_id}/assignments/", headers={"Authorization": f"Bearer {token}"}, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException: return []

@st.cache_data(ttl=10)  # Reduced from 60 to 10 seconds for faster updates
def fetch_all_submissions_cached(class_id, token):
    try:
        response = requests.get(f"{API_URL}/classes/{class_id}/all-assignments-submissions", headers={"Authorization": f"Bearer {token}"}, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.RequestException: return []

# =========================
# Fetch Professor's Classes
# =========================
try:
    response = requests.get(f"{API_URL}/classes/", headers={"Authorization": f"Bearer {st.session_state.token}"})
    response.raise_for_status()
    classes = [c for c in response.json() if st.session_state.user['user_id'] in [p['user_id'] for p in c.get('professors', [])]]
except requests.RequestException as e:
    st.error(f"Error fetching classes: {e}")
    classes = []
    st.stop()

if not classes:
    st.warning("You are not teaching any classes yet.")
    if st.button("Create New Class"): st.switch_page("pages/create_class.py")
    st.stop()

# =========================
# Class and Assignment Selection
# =========================
col1, col2 = st.columns([3, 1])
with col1:
    selected_class = st.selectbox("Select a class to manage:", options=classes, format_func=lambda x: f"{x['name']} ({x['code']})")
with col2:
    if st.button("🔄 Refresh Data", help="Refresh all submissions and assignments", type="secondary"):
        st.cache_data.clear()
        st.rerun()

if selected_class:
    st.markdown('<div class="styled-card">', unsafe_allow_html=True)
    st.subheader("Class Grading Prompt")
    try:
        response = requests.get(f"{API_URL}/classes/{selected_class['id']}/prompt", headers={"Authorization": f"Bearer {st.session_state.token}"})
        if response.status_code == 200:
            class_prompt = response.json()
            if class_prompt and 'prompt' in class_prompt:
                st.code(class_prompt['prompt'], language="text")
                st.write(f"**Title:** {class_prompt.get('title', 'N/A')}")
            else: st.info("No grading prompt is currently assigned to this class.")
        else: st.info("No grading prompt is currently assigned to this class.")
    except Exception as e: st.error(f"Error fetching class prompt: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# Grading & Feedback Section
# =========================
st.markdown("---")
st.header("📝 Grade Student Submissions")
if selected_class:
    assignments = fetch_assignments_cached(selected_class['id'], st.session_state.token)
    if not assignments:
        st.info("No assignments found for this class.")
    else:
        all_submissions_data = fetch_all_submissions_cached(selected_class['id'], st.session_state.token)
        
        submissions_by_assignment = {}
        for submission_data in all_submissions_data:
            if submission_data.get('submissions'):
                assignment_id = submission_data['submissions'][0].get('assignment_id')
                if assignment_id:
                    if assignment_id not in submissions_by_assignment:
                        submissions_by_assignment[assignment_id] = []
                    submissions_by_assignment[assignment_id].append(submission_data)
        
        for assignment in assignments:
            with st.expander(f"Assignment: {assignment['name']}", expanded=False):
                user_submission_list = submissions_by_assignment.get(assignment['id'], [])
                
                if not user_submission_list:
                    st.info("No student submissions for this assignment yet.")
                    continue
                
                for user_data in user_submission_list:
                    latest_sub = user_data['submissions'][0]
                    st.markdown(f"**👨‍🎓 {user_data['username']}** (Latest Submission)")
                    
                    s_col1, s_col2 = st.columns(2)
                    with s_col1:
                        st.markdown("<div class='info-box'>", unsafe_allow_html=True)
                        st.markdown("#### 🤖 AI Grade & Feedback")
                        st.markdown(f"**AI Grade:** {latest_sub.get('ai_grade', 'N/A')}")
                        st.markdown(f"**AI Feedback:** *{latest_sub.get('ai_feedback', 'N/A')}*")
                        st.code(latest_sub.get('code', ''), language="python")
                        st.markdown("</div>", unsafe_allow_html=True)
                    with s_col2:
                        with st.form(f"grade_form_{latest_sub['id']}"):
                            st.markdown("#### 👨‍🏫 Your Grade & Feedback")
                            
                            # FIXED: Safely handle None values before passing to float()
                            current_grade = latest_sub.get('professor_grade')
                            default_value = float(current_grade) if current_grade is not None else 0.0
                            
                            prof_grade = st.number_input(
                                "Final Grade (0-100)", 
                                min_value=0.0, 
                                max_value=100.0, 
                                step=1.0, 
                                value=default_value
                            )
                            prof_feedback = st.text_area("Feedback", value=latest_sub.get('professor_feedback', ""), height=150)
                            
                            if st.form_submit_button("Submit Grade & Feedback"):
                                try:
                                    response = requests.post(
                                        f"{API_URL}/submissions/{latest_sub['id']}/professor-grade",
                                        headers={"Authorization": f"Bearer {st.session_state.token}"},
                                        json={"grade": prof_grade, "feedback": prof_feedback}
                                    )
                                    response.raise_for_status()
                                    st.success(f"Grade updated for {user_data['username']}!")
                                    fetch_all_submissions_cached.clear()
                                    st.rerun()
                                except requests.RequestException as e:
                                    st.error(f"Error updating grade: {e}")
                    st.markdown("---")