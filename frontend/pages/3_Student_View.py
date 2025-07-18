# =========================
# Student View Page - Optimized
# =========================
# This file implements the dashboard for students to view and enroll in classes.
# Students can see their enrolled classes, available classes, and navigate to class details or grades.

import streamlit as st
import requests
import os
from dotenv import load_dotenv
import time
import asyncio
import aiohttp
import json
from datetime import datetime, timedelta

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
    page_title="Student View",
    page_icon="👨‍🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# Custom CSS with new Colors and Transitions
# =========================

st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        /* --- Animation Keyframes (from login.py) --- */
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        /* --- Hide default sidebar --- */
        [data-testid="stSidebarNav"] {
            display: none;
        }
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            animation: fadeIn 0.5s ease-in-out forwards;
        }

        /* --- Theme & Styles (from login.py) --- */
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
        
        /* Header styling */
        .stMarkdown h1 {
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--text-color);
            text-align: center;
            padding-top: 1rem;
        }
        .stMarkdown h3 {
             color: var(--text-color);
             border-bottom: 2px solid var(--border-color);
             padding-bottom: 0.5rem;
             margin-top: 1rem;
        }
        .stMarkdown h4 {
            color: var(--primary-color);
        }

        /* Expander/Card styling */
        .stExpander {
            background-color: var(--card-background-color);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(212, 163, 115, 0.05);
            margin-bottom: 1rem;
            transition: all 0.3s ease-in-out;
        }
        .stExpander:hover {
            box-shadow: 0 8px 24px rgba(212, 163, 115, 0.1);
        }
        .stExpander header {
            font-size: 1.2rem;
            font-weight: 600;
            color: var(--text-color);
        }

        /* --- Input and Button Styling with Transitions --- */
        .stTextInput > div > div > input, .stTextArea > div > textarea {
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 0.75rem 1rem;
            background-color: var(--card-background-color);
            color: var(--text-color);
            transition: all 0.2s ease-in-out;
        }
        .stTextInput > div > div > input:focus, .stTextArea > div > textarea:focus {
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(212, 163, 115, 0.2);
        }

        .stButton > button {
            background-color: var(--primary-color);
            color: var(--text-color);
            border-radius: 8px;
            padding: 0.5rem 1rem;
            font-weight: 600;
            border: 1px solid var(--primary-color);
            transition: all 0.2s ease-in-out;
        }
        .stButton > button:hover {
            background-color: var(--primary-hover-color);
            border-color: var(--primary-hover-color);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(212, 163, 115, 0.15);
        }
        /* Style for secondary/transparent buttons */
        .stButton > button[kind="secondary"] {
             background-color: transparent;
             color: var(--primary-color);
             border: 1px solid var(--primary-color);
        }
         .stButton > button[kind="secondary"]:hover {
             background-color: var(--primary-hover-color);
             color: var(--text-color);
             border-color: var(--primary-hover-color);
         }
    </style>
""", unsafe_allow_html=True)


# =========================
# Performance Optimization Functions
# =========================

@st.cache_data(ttl=10)  # Reduced from 300 to 10 seconds for faster updates
def fetch_classes_cached(token):
    try:
        response = requests.get(f"{API_URL}/classes/", headers={"Authorization": f"Bearer {token}"}, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error fetching classes: {e}")
        return []

@st.cache_data(ttl=10)  # Reduced from 180 to 10 seconds for faster updates
def fetch_assignments_cached(class_id, token):
    try:
        response = requests.get(f"{API_URL}/classes/{class_id}/assignments/", headers={"Authorization": f"Bearer {token}"}, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return []

@st.cache_data(ttl=30)
def fetch_submissions_cached(token):
    try:
        response = requests.get(f"{API_URL}/submissions/", headers={"Authorization": f"Bearer {token}"}, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return []

@st.cache_data(ttl=300)
def fetch_class_prompt_cached(class_id, token):
    try:
        response = requests.get(f"{API_URL}/classes/{class_id}/prompt", headers={"Authorization": f"Bearer {token}"}, timeout=10)
        if response.status_code == 200:
            return response.json().get('prompt', '')
        return ''
    except Exception:
        return ''

def fetch_class_data_optimized(class_ids, token):
    assignments_data = {class_id: fetch_assignments_cached(class_id, token) for class_id in class_ids}
    prompts_data = {class_id: fetch_class_prompt_cached(class_id, token) for class_id in class_ids}
    return assignments_data, prompts_data

# =========================
# Header and Access Control
# =========================
st.markdown('<h1>Student Dashboard</h1>', unsafe_allow_html=True)

if 'user' not in st.session_state:
    st.switch_page("login.py")

if st.session_state.user.get('is_professor'):
    st.error("This page is for students only")
    st.stop()

# =========================
# Performance Monitoring & Data Fetching
# =========================
start_time = time.time()
with st.spinner("Loading classes..."):
    all_classes = fetch_classes_cached(st.session_state.token)

if 'enrolled_classes' not in st.session_state:
    st.session_state.enrolled_classes = []

enrolled_classes = [c for c in all_classes if any(s['user_id'] == st.session_state.user['user_id'] for s in c.get('students', []))]
available_classes = [c for c in all_classes if not any(s['user_id'] == st.session_state.user['user_id'] for s in c.get('students', []))]

if enrolled_classes:
    with st.spinner("Loading assignments and submissions..."):
        enrolled_class_ids = [class_data['id'] for class_data in enrolled_classes]
        assignments_data, prompts_data = fetch_class_data_optimized(enrolled_class_ids, st.session_state.token)
        all_submissions = fetch_submissions_cached(st.session_state.token)

# =========================
# Grade Update Notification System
# =========================
@st.cache_data(ttl=10)
def check_recent_updates_api(token):
    try:
        response = requests.get(f"{API_URL}/submissions/recent-updates", headers={"Authorization": f"Bearer {token}"}, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return []

recent_updates_api = check_recent_updates_api(st.session_state.token)
if recent_updates_api:
    st.success(f"🎉 **New grades available!** {len(recent_updates_api)} submission(s) have been graded recently.")
    for update in recent_updates_api:
        assignment_name = update.get('assignment', {}).get('name', 'Unknown')
        grade = update.get('professor_grade', 'N/A')
        st.info(f"📊 Assignment {assignment_name}: {grade}/100")

# =========================
# Auto-refresh functionality
# =========================
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh > 30:
    st.session_state.last_refresh = time.time()
    fetch_submissions_cached.clear()
    check_recent_updates_api.clear()
    st.rerun()

# =========================
# UI: Enrolled and Available Classes
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
                for professor in class_data['professors']:
                    st.markdown(f"- {professor['name']} ({professor['email']})")
                # Add Go to Home button
                if st.button(f"Go to Home", key=f"go_home_{class_data['id']}"):
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
                        requests.post(
                            f"{API_URL}/classes/{class_data['id']}/enroll",
                            headers={"Authorization": f"Bearer {st.session_state.token}"}
                        ).raise_for_status()
                        st.success(f"Successfully enrolled in {class_data['name']}!")
                        fetch_classes_cached.clear()
                        time.sleep(1)
                        st.rerun()
                    except requests.RequestException as e:
                        st.error(f"Error enrolling in class: {e}")
    else:
        st.info("No available classes to enroll in at the moment.")

st.markdown("---")

# =========================
# Sidebar & Performance Metrics
# =========================
with st.sidebar:
    # Custom Home link logic: set selected_class if missing
    if 'selected_class' not in st.session_state and enrolled_classes:
        st.session_state.selected_class = enrolled_classes[0]
    st.title("🎓 Student Menu")
    st.page_link('pages/3_Student_View.py', label='Student View', icon='👨‍🎓')
    st.page_link('pages/1_Home.py', label='Home', icon='🏠')
    st.page_link('pages/4_Grades_View.py', label='Grades View', icon='📊')
    st.markdown("---")
    if st.button("Logout", use_container_width=True, type="secondary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("login.py")
        
    load_time = time.time() - start_time
    st.markdown("### Performance")
    st.metric("Page Load Time", f"{load_time:.2f}s")
    if st.button("Clear App Cache", type="secondary"):
        st.cache_data.clear()
        st.success("Cache cleared! Refreshing...")
        time.sleep(1)
        st.rerun()

# =========================
# Bottom Navigation (kept from original)
# =========================
nav_col1, nav_col3 = st.columns(2)
with nav_col1:
    if st.button("Refresh Page", type="secondary"):
        st.rerun()
with nav_col3:
    if st.button("Logout", key="bottom_logout", type="secondary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("login.py")